"""Regression guards for wrong CPU architecture and corrupt runtime inputs."""
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1]/'scripts/launch-sketchup.py'
spec = importlib.util.spec_from_file_location('launcher', SOURCE)
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


def pe(machine):
    data = bytearray(134)
    data[:2] = b'MZ'
    struct.pack_into('<I', data, 60, 128)
    data[128:132] = b'PE\0\0'
    struct.pack_into('<H', data, 132, machine)
    return data


class ArchitectureValidation(unittest.TestCase):
    def test_architecture_boundary_and_corrupt_inputs(self):
        with tempfile.TemporaryDirectory(prefix='sketchup-validation-') as directory:
            file = Path(directory)/'a library with spaces.dll'
            for machine, acceptable in [(0x8664, True), (0xaa64, False), (0x14c, False)]:
                with self.subTest(machine=hex(machine)):
                    file.write_bytes(pe(machine))
                    if acceptable:
                        launcher.check_x64(file)
                    else:
                        with self.assertRaisesRegex(ValueError, 'x86-64'):
                            launcher.check_x64(file)
                    self.assertEqual(file.read_bytes(), pe(machine), 'Validation must not modify the input')
            for broken in [b'', b'MZ', b'not an executable', pe(0x8664)[:132]]:
                file.write_bytes(broken)
                with self.assertRaises(ValueError):
                    launcher.check_x64(file)

    def test_missing_file_does_not_create_anything(self):
        with tempfile.TemporaryDirectory(prefix='sketchup-validation-') as directory:
            file = Path(directory)/'missing.dll'
            with self.assertRaises(FileNotFoundError):
                launcher.check_x64(file)
            self.assertFalse(file.exists())


if __name__ == '__main__':
    unittest.main()
