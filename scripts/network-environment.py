#!/usr/bin/env python3
"""Expose existing host CA trust to one private SketchUp environment.

Generated CA bundles and receipts are private installation data. No certificate
is downloaded, no domain is exempted, and TLS validation stays enabled.
"""
import hashlib
import json
import os
from pathlib import Path
import ssl
import tempfile

PROXY_KEYS = ('http_proxy', 'https_proxy', 'all_proxy',
              'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'no_proxy', 'NO_PROXY')


def private_write(path, data):
    """Replace our own generated file atomically; never follow an output link."""
    if path.is_symlink():
        raise ValueError('Generated network configuration must not be a symlink')
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.chmod(0o600)
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def prepare(root, host_environment=None):
    host_environment = dict(os.environ if host_environment is None else host_environment)
    requested = host_environment.get('SSL_CERT_FILE')
    default = ssl.get_default_verify_paths().openssl_cafile
    source = Path(requested or default or '/etc/ssl/certs/ca-certificates.crt')
    source = source.expanduser().resolve(strict=True)
    with source.open('rb') as stream:
        data = stream.read(10 * 1024 * 1024 + 1)
    if len(data) > 10 * 1024 * 1024 or b'PRIVATE KEY' in data:
        raise ValueError('Expected an existing host public CA bundle, without private keys')
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.load_verify_locations(cadata=data.decode('ascii'))
    count = context.cert_store_stats()['x509_ca']
    if not count:
        raise ValueError('Host trust bundle contains no usable CA certificates')
    root = Path(root).resolve(strict=True)
    directory = root/'config/network'
    if directory.is_symlink() or not directory.resolve().is_relative_to(root):
        raise ValueError('Private trust directory escapes the installation')
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    directory.chmod(0o700)
    bundle = directory/'host-ca.pem'
    receipt = directory/'trust-source.json'
    if bundle.is_symlink() or receipt.is_symlink():
        raise ValueError('Generated network configuration must not be a symlink')
    if not bundle.exists() or bundle.read_bytes() != data:
        private_write(bundle, data)
    bundle.chmod(0o600)
    manifest = {'schema': 1, 'source': str(source),
                'sha256': hashlib.sha256(data).hexdigest(), 'ca_count': count,
                'policy': 'Existing host trust; TLS validation enabled; no domain allowlist'}
    private_write(receipt, (json.dumps(manifest, indent=2)+'\n').encode())
    env = {name: str(bundle) for name in
           ('SSL_CERT_FILE', 'CURL_CA_BUNDLE', 'REQUESTS_CA_BUNDLE')}
    # Exact validated GE Wine crypt32 accepts a PEM file here. Imported roots are
    # synchronized at startup; independently added prefix roots remain intact.
    env['WINE_ADDITIONAL_CERTS_DIR'] = str(bundle)
    env['AAG_HOST_CA_BUNDLE'] = str(bundle)
    env['AAG_HOST_CA_SHA256'] = manifest['sha256']
    for key in PROXY_KEYS:
        if key in host_environment:
            env[key] = host_environment[key]
    for key in ('no_proxy', 'NO_PROXY'):
        values = [x.strip() for x in host_environment.get(key, '').split(',') if x.strip()]
        for local in ('localhost', '127.0.0.1', '::1'):
            if local not in values:
                values.append(local)
        env[key] = ','.join(values)
    return env


def redact_environment(env):
    """Keep proxy credentials and internal bypass names out of launch receipts."""
    return {key: '[configured; value omitted]' if key in PROXY_KEYS else value
            for key, value in env.items()}
