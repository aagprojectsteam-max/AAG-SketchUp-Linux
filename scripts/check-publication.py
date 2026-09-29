#!/usr/bin/env python3
"""Scan the staged publication tree; never scan or print private installation data.

This is a deterministic release guard, not a guarantee that every possible secret
can be detected. Review the staged diff and screenshot contents as well.
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {'.gitignore', 'LICENSE', 'README.md', 'INSTALL.md', 'TROUBLESHOOTING.md',
    'docs/BASELINE.md', 'docs/CANONICAL-PATH.md', 'docs/CHANGELOG.md', 'docs/CLEANUP.md',
    'docs/CODEX-HANDOFF.md', 'docs/FINAL-REPORT.md', 'docs/GOLDEN-STATE.md',
    'docs/GRAPHICS.md', 'docs/HISTORY.md', 'docs/INSTALL.md', 'docs/ROOT-CAUSE.md',
    'docs/TEST-MATRIX.md', 'docs/TROUBLESHOOTING.md', 'docs/UNINSTALL-ROLLBACK.md',
    'docs/acceptance.json', 'docs/images/aa-before.png', 'docs/images/aa-4x.png',
    'docs/images/aa-after.png', 'scripts/collect-diagnostics.py',
    'scripts/install-launcher.py', 'scripts/launch-sketchup.py',
    'scripts/patch-wine-touch.py', 'scripts/prepare-installation.py',
    'scripts/check-publication.py', 'tests/test_launcher_validation.py',
    'tests/test_wine_touch_patch.py'}
ALLOWED.update({'docs/ROOT-CAUSE.md', 'scripts/runtime-exec.py', 'docs/TEST-MATRIX.md', 'tests/popup-present-smoke.c', 'docs/CODEX-HANDOFF.md', 'scripts/popup-present.c', 'docs/INSTALL.md', 'docs/CANONICAL-PATH.md', 'docs/HISTORY.md', 'docs/PLUGINS.md', 'scripts/migrate-plugin.py', 'docs/CLEANUP.md', 'docs/PLUGIN-MIGRATION.md', 'docs/WINDOW-PAINTING.md', 'docs/WINDOWS-PLUGIN-INVENTORY.md', 'docs/BASELINE.md', 'docs/TROUBLESHOOTING.md', 'scripts/pe_metadata.py', 'tests/test_plugin_migration.py', 'docs/plugin-acceptance.json', 'scripts/build-popup-helper.py', 'docs/PLUGIN-MIGRATION-REPORT.md', 'docs/GRAPHICS.md', 'docs/UNINSTALL-ROLLBACK.md', 'docs/FINAL-REPORT.md', 'scripts/audit-plugins.py', 'docs/CHANGELOG.md', 'docs/PLUGIN-USER-DATA.md', 'docs/GOLDEN-STATE.md', 'artifacts/production-plugin-manifest.json', 'docs/PLUGIN-GOLDEN-DELTA.md'})
ALLOWED.update({
    'artifacts/current-golden-baseline.json',
    'config/compatibility-rules.json',
    'docs/CODEX-UPDATE-PROMPT.md',
    'docs/GOLDEN-HISTORY.md',
    'docs/UPDATE-FRAMEWORK-REPORT.md',
    'docs/UPDATE.md',
    'docs/update-framework-acceptance.json',
    'docs/updates/TEMPLATE.md',
    'scripts/prepare-update.py',
    'tests/test_update_workflow.py',
    'tests/update-model.rb',
})
ALLOWED.update({'docs/network-acceptance.json', 'tests/network-probe.c', 'tests/network-wininet.c', 'docs/NETWORKING.md', 'scripts/network-environment.py', 'tests/test_network_environment.py', 'scripts/network-trust.rb'})
ALLOWED.update({'scripts/keyboard-environment.py', 'tests/test_keyboard_environment.py', 'docs/HEBREW-INPUT.md', 'docs/hebrew-input-acceptance.json'})
ALLOWED.update({'tests/input-win32.c', 'tests/input-gtk.py', 'tests/input-sketchup.rb'})
PATTERNS = {
    'certificate material': r'-----BEGIN (?:TRUSTED )?CERTIFICATE-----',
    'credential token': r'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,}|sk-(?:proj-)?[A-Za-z0-9_-]{30,}|AKIA[A-Z0-9]{16})\b',
    'private key': r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
    'private absolute path': r'/(?:home/[^\s/]+|mnt/data)/',
    'account email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
    'Steam account identifier': r'(?<![0-9a-f])[0-9]{17}(?![0-9a-f])',
}

def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])

def main():
    names = git('diff', '--cached', '--name-only', '--diff-filter=ACMR', '-z').decode().split('\0')
    # Include the complete index so unchanged files are scanned on later releases.
    names = [x for x in git('ls-files', '-z').decode().split('\0') if x]
    issues = []; manifest = {}
    for name in names:
        if name not in ALLOWED:
            issues.append({'path': name, 'issue': 'outside explicit publication allowlist'})
            continue
        data = git('show', ':'+name)
        manifest[name] = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
        if len(data) > 200_000 or data.startswith((b'MZ', b'\x7fELF', b'PK\x03\x04')):
            issues.append({'path': name, 'issue': 'binary/archive/oversize material'})
            continue
        if name.endswith('.png'):
            if not data.startswith(b'\x89PNG\r\n\x1a\n'):
                issues.append({'path': name, 'issue': 'invalid image signature'})
            pos = 8
            while pos+12 <= len(data):
                size = int.from_bytes(data[pos:pos+4], 'big'); kind = data[pos+4:pos+8]
                if kind not in (b'IHDR', b'IDAT', b'IEND'):
                    issues.append({'path': name, 'issue': 'image has unexpected metadata chunk'})
                pos += size+12
            continue
        try:
            text = data.decode('utf-8')
        except UnicodeDecodeError:
            issues.append({'path': name, 'issue': 'unexpected non-text file'})
            continue
        for label, pattern in PATTERNS.items():
            if re.search(pattern, text):
                issues.append({'path': name, 'issue': label})
        if name.endswith('.md'):
            for link in re.findall(r'\]\(([^)]+)\)', text):
                target = link.split('#')[0]
                if not target or '://' in target:
                    continue
                if not (ROOT/name).parent.joinpath(target).exists():
                    issues.append({'path': name, 'issue': 'missing local documentation link', 'target': target})
    print(json.dumps({'status': 'PASS' if not issues else 'FAIL', 'files': len(names),
                      'total_bytes': sum(x['bytes'] for x in manifest.values()),
                      'issues': issues, 'manifest': manifest}, indent=2))
    return 1 if issues else 0

if __name__ == '__main__': sys.exit(main())
