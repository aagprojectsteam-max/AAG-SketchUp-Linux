"""Safety boundaries; optional validation against a user-provided stock Wine DLL."""
import hashlib
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1]/'scripts/patch-wine-touch.py'
spec = importlib.util.spec_from_file_location('touch_patch', SOURCE)
patcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patcher)

class TouchPatchSafety(unittest.TestCase):
    def test_unknown_dll_is_not_modified(self):
        with tempfile.TemporaryDirectory() as directory:
            dll = Path(directory)/'user32.dll'
            original = b'Not the supported open-source Wine binary'
            dll.write_bytes(original)
            result = subprocess.run(['python3', str(SOURCE), str(dll)], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(dll.read_bytes(), original)
            self.assertEqual(list(Path(directory).iterdir()), [dll])

    @unittest.skipUnless(os.environ.get('AAG_STOCK_WINE_USER32'), 'Provide your own exact stock Wine DLL for integration validation')
    def test_stock_export_preservation_and_idempotence(self):
        original = Path(os.environ['AAG_STOCK_WINE_USER32']).read_bytes()
        self.assertEqual(hashlib.sha256(original).hexdigest(), patcher.STOCK)
        with tempfile.TemporaryDirectory() as directory:
            dll = Path(directory)/'user32.dll'
            dll.write_bytes(original)
            for _ in range(2):
                subprocess.run(['python3', str(SOURCE), str(dll)], check=True, capture_output=True)
            result = dll.read_bytes()
            self.assertEqual(hashlib.sha256(result).hexdigest(), '4e1251c8074cef40260caf36a9c84db42be33400af88a15c39fa5f638c42df65')
            before = patcher.PE(original).entries()
            after = patcher.PE(result).entries()
            self.assertEqual({k: after[k] for k in before}, before)
            self.assertEqual(set(after)-set(before), {patcher.NAME})
            self.assertEqual(after[patcher.NAME][1:], before[patcher.TARGET][1:])
            self.assertEqual(dll.with_name('user32.dll.aag-original').read_bytes(), original)

if __name__ == '__main__': unittest.main()
