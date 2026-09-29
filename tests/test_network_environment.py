"""Guard host trust propagation, private output and launch-log privacy."""
import json
import os
from pathlib import Path
import runpy
import ssl
import tempfile
import unittest
from unittest.mock import patch

api = runpy.run_path(str(Path(__file__).resolve().parents[1]/'scripts/network-environment.py'))

class HostTrustTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='sketchup trust ')
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base/'private application'
        self.root.mkdir()
        self.ca = self.base/'existing host.pem'
        self.ca.write_bytes(Path(ssl.get_default_verify_paths().cafile).read_bytes())
        self.env = {'SSL_CERT_FILE': str(self.ca)}

    def test_refresh_uses_host_bytes_and_private_permissions(self):
        env = api['prepare'](self.root, self.env)
        bundle = Path(env['SSL_CERT_FILE'])
        self.assertEqual(bundle.read_bytes(), self.ca.read_bytes())
        self.assertEqual(bundle.stat().st_mode & 0o777, 0o600)
        self.assertEqual(bundle.parent.stat().st_mode & 0o777, 0o700)
        self.ca.write_bytes(self.ca.read_bytes()+b'\n')
        api['prepare'](self.root, self.env)
        self.assertEqual(bundle.read_bytes(), self.ca.read_bytes())
        context=ssl.create_default_context(cafile=str(bundle))
        self.assertEqual(context.verify_mode,ssl.CERT_REQUIRED)
        self.assertTrue(context.check_hostname)

    def test_output_links_cannot_overwrite_another_file(self):
        for name in ('host-ca.pem','trust-source.json'):
            with self.subTest(name=name):
                target=self.base/'unrelated';target.write_text('preserve')
                directory=self.root/'config/network';directory.mkdir(parents=True,exist_ok=True)
                link=directory/name;link.symlink_to(target)
                try:
                    with self.assertRaises(ValueError):api['prepare'](self.root,self.env)
                    self.assertEqual(target.read_text(),'preserve')
                finally:link.unlink()

    def test_directory_escape_is_refused(self):
        (self.root/'config').symlink_to(self.base)
        with self.assertRaises(ValueError):api['prepare'](self.root,self.env)
        self.assertFalse((self.base/'network').exists())

    def test_invalid_source_does_not_replace_working_trust(self):
        bundle=Path(api['prepare'](self.root,self.env)['SSL_CERT_FILE'])
        original=bundle.read_bytes()
        for invalid in (b'not a CA', b'PRIVATE KEY'):
            self.ca.write_bytes(invalid)
            with self.assertRaises((ValueError,ssl.SSLError)):api['prepare'](self.root,self.env)
            self.assertEqual(bundle.read_bytes(),original)

    def test_missing_explicit_source_fails_closed(self):
        self.env['SSL_CERT_FILE']=str(self.base/'missing')
        with self.assertRaises(FileNotFoundError):api['prepare'](self.root,self.env)
        self.assertFalse((self.root/'config').exists())

    def test_proxy_is_inherited_and_local_callbacks_exempted(self):
        self.env.update(HTTPS_PROXY='http://user:private-value@127.0.0.1:8080',NO_PROXY='internal.invalid')
        env=api['prepare'](self.root,self.env)
        self.assertEqual(env['HTTPS_PROXY'],self.env['HTTPS_PROXY'])
        self.assertEqual(set(env['NO_PROXY'].split(',')),{'internal.invalid','localhost','127.0.0.1','::1'})
        receipt=(self.root/'config/network/trust-source.json').read_text()
        self.assertNotIn('private-value',receipt)
        self.assertNotIn('private-value',json.dumps(api['redact_environment'](env)))
        launcher=runpy.run_path(str(Path(__file__).resolve().parents[1]/'scripts/launch-sketchup.py'))
        self.assertNotIn('private-value',json.dumps(launcher['receipt_environment'](env)))

if __name__=='__main__':unittest.main()
