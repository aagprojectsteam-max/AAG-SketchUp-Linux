"""Exercise refusal boundaries and a real interrupted-copy receipt."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
spec=importlib.util.spec_from_file_location('migrate',Path(__file__).resolve().parents[1]/'scripts/migrate-plugin.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class MigrationGuards(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.src=self.root/'source';self.dst=self.root/'target'
        self.src.mkdir();(self.src/'Demo.rb').write_text('# original fixture')
    def test_overlap_and_windows(self):
        for dst in [self.src,self.src/'nested',self.root]:
            with self.assertRaisesRegex(ValueError,'overlap'):m.plan(self.src,dst,'Demo')
        win=self.root/'windows';(win/'Windows').mkdir(parents=True);(win/'Users').mkdir()
        with self.assertRaisesRegex(ValueError,'Windows'):m.plan(self.src,win/'Plugins','Demo')
    def test_root_and_descendant_symlinks(self):
        (self.src/'Demo').symlink_to(self.root,target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'symlink'):m.plan(self.src,self.dst,'Demo')
        (self.src/'Demo').unlink();(self.src/'Demo').mkdir();(self.src/'Demo/link').symlink_to(self.src/'Demo.rb')
        with self.assertRaisesRegex(ValueError,'symlink'):m.plan(self.src,self.dst,'Demo')
    def test_broken_destination_link(self):
        self.dst.mkdir();(self.dst/'Demo.rb').symlink_to(self.root/'missing')
        with self.assertRaisesRegex(ValueError,'already exists'):m.plan(self.src,self.dst,'Demo')
    def test_partial_copy_receipt(self):
        (self.src/'Demo').mkdir();second=self.src/'Demo/data.rb';second.write_text('# second')
        files=m.plan(self.src,self.dst,'Demo');second.write_text('# changed after audit')
        receipt=self.root/'receipt.json';report={}
        with self.assertRaisesRegex(ValueError,'changed'):m.copy_files(self.src,self.dst,files,receipt,report)
        self.assertEqual(report['state'],'PARTIAL_COPY_REQUIRES_REVIEW')
        self.assertEqual(report['copied'],['Demo.rb']);self.assertEqual(report['current_file'],'Demo/data.rb')
        self.assertTrue((self.dst/'Demo.rb').is_file());self.assertFalse((self.dst/'Demo/data.rb').exists())
        self.assertIn('PARTIAL_COPY_REQUIRES_REVIEW',receipt.read_text())
    def test_success_and_source_unchanged(self):
        files=m.plan(self.src,self.dst,'Demo');report={}
        m.copy_files(self.src,self.dst,files,self.root/'receipt.json',report)
        self.assertEqual(report['state'],'COPIED_AND_VERIFIED')
        self.assertEqual(m.sha256(self.src/'Demo.rb'),m.sha256(self.dst/'Demo.rb'))

if __name__=='__main__':unittest.main()
