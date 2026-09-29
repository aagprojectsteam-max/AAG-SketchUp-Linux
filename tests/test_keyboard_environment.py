"""Guard the shared-display repair boundary and rollback behavior."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('keyboard',Path(__file__).resolve().parents[1]/'scripts/keyboard-environment.py')
k=importlib.util.module_from_spec(spec);spec.loader.exec_module(k)
US='name[group1]="English (US)";'
PAIR=US+' name[group2]="Hebrew"; hebrew_aleph'
CONFIG=k.source_config([('xkb','us'),('xkb','il')],'pc105+inet',['grp:alt_shift_toggle'])

class KeyboardRepair(unittest.TestCase):
 def test_empty_gvariant_arrays_are_supported(self):
  for value in ['@as []','@a(ss) []']:
   with patch.object(k,'run',return_value=value):self.assertEqual(k.setting('unused'),[])
  self.assertEqual(k.source_config([('xkb','us'),('xkb','il')],'',[])['model'],'')
 def test_source_boundary(self):
  for sources in [[('xkb','us')],[('ibus','hebrew')],[('xkb','us'),('xkb','il+phonetic')],[('xkb','us'),('xkb','il'),('xkb','de')]]:
   self.assertIsNone(k.source_config(sources,'pc105',[]))
  self.assertEqual(k.source_config([('xkb','il'),('xkb','us')],'pc105',[])['layouts'],['il','us'])
  with self.assertRaises(ValueError):k.source_config([('xkb','us'),('xkb','il')],'pc105',['bad\noption'])
 def test_only_demonstrated_map_is_replaced(self):
  self.assertEqual(k.action(CONFIG,US,{'layout':'us'}),'REPAIR_US_ONLY_MAP')
  self.assertEqual(k.action(CONFIG,PAIR,{'layout':'us,il'}),'ALREADY_PRESENT')
  for mapping,props in [(US,{'layout':'us','variant':'dvorak'}),(US+' name[group2]="German";',{'layout':'us'}),('custom',{'layout':'us'})]:
   self.assertEqual(k.action(CONFIG,mapping,props),'UNSUPPORTED_MAP_REVIEW_REQUIRED')
 def test_other_sessions_do_not_run_commands(self):
  with patch.object(k,'run') as command:
   self.assertEqual(k.prepare('/unused',{'XDG_SESSION_TYPE':'x11'})['status'],'NOT_APPLICABLE')
   command.assert_not_called()
 def exercise(self,fail=False,present=False):
  calls=[];maps=iter([PAIR if present else US,US if fail else PAIR])
  def command(argv,**kwargs):
   calls.append(argv)
   if argv[0]=='xdpyinfo':return 'XWAYLAND'
   if argv[:2]==['xkbcomp','-xkb']:return next(maps)
   if '-query' in argv:return 'rules: evdev\nmodel: pc105\nlayout: us'
   if argv[0]=='ibus':return 'xkb:il::heb'
   return ''
  values={'sources':[('xkb','us'),('xkb','il')],'xkb-model':'pc105+inet','xkb-options':['grp:alt_shift_toggle']}
  with tempfile.TemporaryDirectory() as tmp,patch.object(k,'run',side_effect=command),patch.object(k,'setting',side_effect=values.__getitem__),patch.object(k,'lock_group') as lock:
   env={'XDG_SESSION_TYPE':'wayland','XDG_CURRENT_DESKTOP':'ubuntu:GNOME','DISPLAY':':0'}
   if fail:
    with self.assertRaisesRegex(RuntimeError,'did not reach'):k.prepare(tmp,env)
    self.assertEqual(calls[-1],['xkbcomp',str(Path(tmp)/'xwayland-before.xkb'),':0'])
    self.assertIn(['setxkbmap','-display',':0','-model','pc105','-layout','us','-rules','evdev','-variant','','-option',''],calls)
   else:
    result=k.prepare(tmp,env)
    self.assertEqual(result['status'],'ALREADY_PRESENT' if present else 'REPAIRED')
    if present:
     lock.assert_not_called();self.assertFalse(list(Path(tmp).iterdir()))
    else:
     lock.assert_called_once_with(':0',1)
     self.assertEqual((Path(tmp)/'xwayland-before.xkb').stat().st_mode & 0o777,0o600)
   return calls
 def test_hebrew_initial_source_preserved(self):self.exercise()
 def test_failed_validation_restores_map_and_rules(self):self.exercise(fail=True)
 def test_idempotent_when_bilingual_map_exists(self):
  self.assertFalse(any(c[0]=='setxkbmap' and '-query' not in c for c in self.exercise(present=True)))
