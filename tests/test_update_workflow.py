"""Safety/state tests use synthetic PE files and disposable roots, never Windows."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS=Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0,str(SCRIPTS))
from pe_metadata import inspect_pe,sha256
spec=importlib.util.spec_from_file_location('update_workflow',SCRIPTS/'prepare-update.py')
u=importlib.util.module_from_spec(spec);spec.loader.exec_module(u)


def pe_file(path,machine=0x8664,build='26.1.252'):
    data=bytearray(2048);data[:2]=b'MZ';struct.pack_into('<I',data,60,128);data[128:132]=b'PE\0\0'
    struct.pack_into('<HH',data,132,machine,1);struct.pack_into('<H',data,148,240)
    opt=152;struct.pack_into('<H',data,opt,0x20b);struct.pack_into('<I',data,opt+60,512)
    table=opt+240;data[table:table+8]=b'.rsrc\0\0\0';struct.pack_into('<4I',data,table+8,1024,4096,1024,512)
    struct.pack_into('<13I',data,512,0xfeef04bd,0x10000,26<<16,0,26<<16,0,0,0,0,0,0,0,0)
    # A bounded StringFileInfo String block, intentionally different from fixed version.
    start=576;key='FileVersion\0'.encode('utf-16le');value=(build+'\0').encode('utf-16le')
    at=(start+6+len(key)+3)//4*4;size=at+len(value)-start
    struct.pack_into('<HHH',data,start,size,len(build)+1,1);data[start+6:start+6+len(key)]=key;data[at:at+len(value)]=value
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data);return path


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory(prefix='aag-update-test-');self.addCleanup(self.t.cleanup);self.base=Path(self.t.name)
        self.current=self.base/'current';self.current.mkdir();self.candidate=self.base/'candidate';self.backup=self.base/'backup';self.backup.mkdir()
    def model(self,state='BASE_TESTING'):
        self.candidate.mkdir(exist_ok=True)
        m={'schema':1,'candidate_id':'test-id','root':str(self.candidate),'current_root':str(self.current),
           'rollback_root':str(self.backup),'sources':{'app':str(self.current/'app'),'content':str(self.current/'content'),'runtime':str(self.current/'runtime')},
           'state':state,'current_version':'26.1.252','runtime':{'proton_version':'test'},'preflight':{'status':'PASS'},'classification':'SAME_BUILD_REINSTALL','diff':{'application':{},'content':{}},'framework_changes':{},'old_fixes':{},'plugin_revalidation_plan':[], 'candidate_version':'26.1.252','initialized':True,'plugin_policy':'revalidate','history':[],'test_status':{}}
        u.store(m);return m
    def evidence(self,m):
        e=u.regression_template(m);e['reviewer']='local test reviewer';e['evidence']=['disposable test fixture'];e['base_gates']=dict.fromkeys(u.BASE_GATES,'PASS');return e
    def test_actual_string_version_over_fixed_header(self):
        x=inspect_pe(pe_file(self.base/'app.exe'));self.assertEqual(x['file_version'],'26.0.0.0');self.assertEqual(u.version(x),'26.1.252')
    def test_version_conflict_and_missing(self):
        for x in ({'file_version':'26.0.0.0'},{'version_strings':{'FileVersion':['26.1.252'],'ProductVersion':['27.0.1']}}):
            with self.assertRaises(ValueError):u.version(x)
    def test_pe_architecture_and_hash(self):
        for machine,name in ((0x8664,'x86-64'),(0xaa64,'ARM64'),(0x14c,'x86')):
            f=pe_file(self.base/'library.dll',machine);before=f.read_bytes();x=inspect_pe(f);self.assertEqual(x['architecture'],name);self.assertEqual(x['sha256'],sha256(f));self.assertEqual(f.read_bytes(),before)
    def test_malformed_pe(self):
        p=self.base/'bad';p.write_bytes(b'MZ');self.assertEqual(inspect_pe(p)['architecture'],'INVALID_PE')
    def test_production_overlap_both_directions(self):
        for p in (self.current,self.current/'candidate',self.base):
            with self.assertRaises(ValueError):u.path_guard(p,[self.current],new=True)
    def test_existing_and_symlink_destination(self):
        for p in (self.current,):
            with self.assertRaises(ValueError):u.path_guard(p,[],new=True)
        link=self.base/'alias';link.symlink_to(self.current,target_is_directory=True)
        with self.assertRaises(ValueError):u.path_guard(link/'new',[],new=True)
    def test_windows_destination_guard(self):
        win=self.base/'WindowsDisk';(win/'Windows').mkdir(parents=True);(win/'Users').mkdir()
        with self.assertRaises(ValueError):u.path_guard(win/'new',[],new=True)
    def test_missing_application(self):
        with self.assertRaisesRegex(ValueError,'Missing SketchUp'):u.application_audit(self.current)
    def test_wrong_architecture_blocks_application(self):
        pe_file(self.current/'SketchUp.exe',0xaa64)
        with self.assertRaisesRegex(ValueError,'architecture'):u.application_audit(self.current)
    def test_wrong_critical_dll_reported(self):
        pe_file(self.current/'SketchUp.exe');pe_file(self.current/'msvcp140.dll',0xaa64)
        self.assertEqual(u.application_audit(self.current)['wrong_architecture'],['msvcp140.dll'])
    def test_missing_content_and_complete_content(self):
        self.assertIn('Styles/StyleTemplate.skp',u.content_audit(self.current)['missing'])
        for n in u.RULES['content_directories']:
            (self.current/n).mkdir();(self.current/n/('StyleTemplate.skp' if n=='Styles' else 'fixture')).write_bytes(b'original test fixture')
        self.assertEqual(u.content_audit(self.current)['missing'],[])
    def test_content_link_not_followed(self):
        (self.current/'outside').symlink_to(self.base/'missing')
        with self.assertRaisesRegex(ValueError,'symlink'):u.content_audit(self.current)
    def test_manifest_diff_does_not_modify_files(self):
        p=pe_file(self.current/'SketchUp.exe');before=p.read_bytes();m=u.file_manifest(self.current)
        self.assertEqual(m['SketchUp.exe']['sha256'],sha256(p));self.assertEqual(u.compare(m,m),{'SketchUp.exe':'UNCHANGED'});self.assertEqual(before,p.read_bytes())
    def test_four_touch_branches(self):
        t=u.RULES['touch'];cases=[({'sha256':t['stock_sha256'],'exports':[]},'EXACT_PATCH_ELIGIBLE'),({'sha256':t['patched_sha256'],'exports':[t['export']]},'NO_OP'),({'sha256':'other','exports':[]},'REQUIRES_REVIEW'),({'sha256':'future','exports':[t['export']]},'TEST_NATIVE_NO_LEGACY_PATCH')]
        for meta,action in cases:self.assertEqual(u.touch_decision(meta,t['runtime'])['action'],action)
        self.assertEqual(u.touch_decision(cases[0][0],'new-runtime')['action'],'REQUIRES_REVIEW')
    def test_update_classification(self):
        self.assertEqual(u.classify('26.1.252','26.1.252',False,False),'SAME_BUILD_REINSTALL')
        self.assertEqual(u.classify('26.1.252','26.1.253',True,False),'PATCH_UPDATE')
        self.assertEqual(u.classify('26.1.252','26.2.1',True,False),'MINOR_UPDATE')
        self.assertEqual(u.classify('26.1.252','27.0.1',True,False),'MAJOR_UPDATE')
        self.assertEqual(u.classify('26.1.252','26.1.252',False,True),'RUNTIME_ONLY_CHANGE')
        self.assertEqual(u.classify('26.1.252','26.1.252',False,False,True),'PLUGIN_ONLY_CHANGE')
        self.assertEqual(u.classify('26.1.252','26.1.252',True,False),'UNKNOWN')
    def test_runtime_environment_preserves_home_and_nonsteam_mode(self):
        m=self.model();m['runtime'].update(proton_directory='GE-Proton10-25',container_directory='SteamLinuxRuntime_sniper')
        u.save(self.candidate/'candidate-isolation.json',{'protected_readonly':[str(self.current)]})
        env=u.command_env(m)
        self.assertEqual(env['HOME'],os.environ['HOME']);self.assertEqual(env['UMU_ID'],'umu-sketchup');self.assertEqual(env['STEAM_COMPAT_PROTON'],'1')
        self.assertNotIn('LD_PRELOAD',env);self.assertNotIn('WINEPREFIX',env)
    def audit_fixture(self):
        pe_file(self.current/'app/SketchUp.exe');pe_file(self.current/'app/msvcp140.dll')
        content=self.current/'compatdata/pfx/drive_c/ProgramData/SketchUp/SketchUp 2026/SketchUp'
        for name in u.RULES['content_directories']:
            p=content/name/('StyleTemplate.skp' if name=='Styles' else 'fixture');p.parent.mkdir(parents=True);p.write_bytes(b'test resource')
        (self.current/'runtime').mkdir()
        exe=pe_file(self.backup/'installation/app/SketchUp.exe');u.save(self.backup/'manifest.json',{'files':{'app/SketchUp.exe':{'sha256':sha256(exe)}}})
        args=argparse.Namespace(current_root=self.current,candidate_root=self.candidate,app_source=self.current/'app',content_source=content,runtime_source=self.current/'runtime',rollback_root=self.backup,content_version='26.1.252',source_note='legitimate synthetic fixture',plugin_policy='revalidate',protect_root=[])
        runtime={'files':{},'sha256':'fixture-runtime','proton_version':'GE-Proton10-25','touch':{'action':'NO_OP'},'proton_directory':'GE-Proton10-25'}
        return args,runtime
    def test_complete_audit_no_write_and_manifest_generation(self):
        args,runtime=self.audit_fixture();before=u.file_manifest(self.base)
        with patch.object(u,'runtime_audit',return_value=runtime):m=u.audit(args)
        self.assertEqual(m['preflight']['status'],'PASS');self.assertEqual(m['candidate_version'],'26.1.252');self.assertEqual(m['known_build'],'REQUIRES_AUDIT')
        self.assertEqual(before,u.file_manifest(self.base));self.assertFalse(self.candidate.exists())
    def test_insufficient_disk_is_a_preflight_failure(self):
        args,runtime=self.audit_fixture()
        with patch.object(u,'runtime_audit',return_value=runtime),patch.object(u.shutil,'disk_usage',return_value=argparse.Namespace(free=0)):
            m=u.audit(args)
        self.assertEqual(m['preflight']['status'],'FAIL');self.assertIn('Insufficient free disk space',m['preflight']['errors']);self.assertFalse(self.candidate.exists())
    def test_missing_source_is_refused_without_writes(self):
        args,runtime=self.audit_fixture();args.app_source=self.base/'absent';before=u.file_manifest(self.base)
        with self.assertRaises(FileNotFoundError):u.audit(args)
        self.assertEqual(before,u.file_manifest(self.base))
    def test_incomplete_runtime_is_refused(self):
        with self.assertRaisesRegex(ValueError,'complete Proton'):u.runtime_audit(self.current)
    def test_reject_and_cleanup_plan_preserve_payload(self):
        import contextlib,io
        m=self.model();payload=self.candidate/'retained';payload.write_text('keep')
        with patch.object(sys,'argv',['prepare-update.py','reject','--candidate-root',str(self.candidate),'--reason','self-test only']),contextlib.redirect_stdout(io.StringIO()):u.main()
        self.assertEqual(u.load(self.candidate)['state'],'REJECTED')
        out=io.StringIO()
        with patch.object(sys,'argv',['prepare-update.py','cleanup-plan','--candidate-root',str(self.candidate),'--dry-run']),contextlib.redirect_stdout(out):u.main()
        self.assertFalse(json.loads(out.getvalue())['deleted']);self.assertEqual(payload.read_text(),'keep')
    def test_dry_run_on_mutation_is_refused(self):
        m=self.model();before=u.file_manifest(self.candidate)
        with patch.object(sys,'argv',['prepare-update.py','reject','--candidate-root',str(self.candidate),'--reason','test','--dry-run']):
            with self.assertRaisesRegex(ValueError,'dry-run'):u.main()
        self.assertEqual(before,u.file_manifest(self.candidate))
    def test_template_never_claims_pass(self):
        e=u.regression_template(self.model());self.assertTrue(all(x=='NOT_TESTED' for x in e['base_gates'].values()))
    def test_base_requires_full_review_and_correct_candidate(self):
        m=self.model();e=self.evidence(m);e['base_gates']['LINE']='NOT_TESTED'
        with self.assertRaises(ValueError):u.validate(m,e,'base')
        self.assertEqual(m['state'],'BASE_TESTING');e=self.evidence(m);e['candidate_id']='other'
        with self.assertRaises(ValueError):u.validate(m,e,'base')
    def test_base_transition_and_order(self):
        m=self.model();e=self.evidence(m)
        with self.assertRaises(ValueError):u.validate(m,e,'plugins')
        u.validate(m,e,'base');self.assertEqual(u.load(self.candidate)['state'],'BASE_PASS')
    def test_plugin_partial_and_deferred_do_not_fail(self):
        m=self.model('BASE_PASS');e=self.evidence(m);e['plugins']=[{'name':'optional','result':'USER_ACTION_DEFERRED','installed':False,'evidence':'user choice'}]
        u.validate(m,e,'plugins');self.assertEqual(m['state'],'PLUGIN_PARTIAL')
    def test_installed_untested_plugin_cannot_pass(self):
        m=self.model('BASE_PASS');e=self.evidence(m);e['plugins']=[{'name':'bad','result':'NOT_TESTED','installed':True,'evidence':'not run'}]
        with self.assertRaises(ValueError):u.validate(m,e,'plugins')
    def test_ready_requires_plugin_validation(self):
        m=self.model('BASE_PASS')
        with self.assertRaises(ValueError):u.validate(m,{},'ready')
    def test_manifest_relocation_is_refused(self):
        m=self.model();m['root']=str(self.base/'other');u.store(dict(m,root=str(self.candidate)))
        data=json.loads((self.candidate/'candidate-manifest.json').read_text());data['root']=str(self.base/'other');u.save(self.candidate/'candidate-manifest.json',data)
        with self.assertRaises(ValueError):u.load(self.candidate)
    def test_rollback_hash_corruption(self):
        p=self.backup/'installation/app/SketchUp.exe';pe_file(p);u.save(self.backup/'manifest.json',{'files':{'app/SketchUp.exe':{'sha256':sha256(p)}}})
        self.assertEqual(u.rollback_verify(self.backup)['verified_files'],1);p.write_bytes(b'changed')
        with self.assertRaises(ValueError):u.rollback_verify(self.backup)
    def test_output_guard_never_writes_source(self):
        m=self.model();target=self.current/'report.json'
        with self.assertRaises(ValueError):u.private_report(target,m)
        self.assertFalse(target.exists())
    def test_unknown_candidate_configuration_refused(self):
        m=self.model();m['known_build']='REQUIRES_AUDIT';m['runtime']={'proton_directory':'GE-Proton10-25'}
        with self.assertRaises(ValueError):u.configure_known(m,self.base/'ucrt',{})
    def test_promotion_refuses_non_ready_and_changed_candidate(self):
        m=self.model()
        with self.assertRaises(ValueError):u.promote(m,[],self.base/'transaction',self.base/'metadata')
        m['state']='READY_FOR_PROMOTION';m['accepted_fingerprint']={'wrong':'hash'}
        with self.assertRaisesRegex(ValueError,'changed'):u.promote(m,[],self.base/'transaction',self.base/'metadata')
        self.assertFalse((self.base/'transaction').exists())
    def promotion_fixture(self):
        m=self.model('READY_FOR_PROMOTION')
        (self.candidate/'config/icons').mkdir(parents=True);(self.candidate/'config/icons/sketchup.png').write_bytes(b'original icon fixture')
        exe=pe_file(self.backup/'installation/app/SketchUp.exe')
        u.save(self.backup/'manifest.json',{'files':{'app/SketchUp.exe':{'sha256':sha256(exe)}}})
        meta={'candidate_id':m['candidate_id'],'version':m['candidate_version'],'new_tag':'new-test-tag','rollback_root':m['rollback_root'],
              'repository':str(self.base/'repo'),'update_report':'docs/updates/test.md','reviewed_files':{},'backward_file_warning_reviewed':True,'plugin_changes_reviewed_by_user':True,'startup_wm_class':'steam_app_0'}
        for name in ['README.md','artifacts/current-golden-baseline.json','docs/GOLDEN-HISTORY.md','docs/PLUGINS.md','docs/TEST-MATRIX.md',meta['update_report']]:
            f=Path(meta['repository'])/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_text('reviewed test metadata');meta['reviewed_files'][name]=sha256(f)
        mf=self.base/'metadata.json';u.save(mf,meta)
        entries=[self.base/'Apps.desktop',self.base/'Desktop.desktop']
        for f in entries:f.write_text('[Desktop Entry]\nExec='+u.desktop_quote(str(self.current/'bin/launch-sketchup.py'))+' %f\nIcon=old\nName=SketchUp 2026\nStartupWMClass=steam_app_0\n')
        m['accepted_fingerprint']=u.fingerprint(self.candidate);u.store(m)
        return m,entries,mf
    def test_promotion_and_rollback_keep_old_root(self):
        m,entries,mf=self.promotion_fixture();before=[p.read_text() for p in entries];keep=self.current/'keep';keep.write_text('untouched')
        with patch.object(u.subprocess,'run',return_value=argparse.Namespace(returncode=1)):
            result=u.promote(m,entries,self.base/'transaction',mf)
        self.assertEqual(result['state'],'AWAITING_POST_PROMOTION_GUI');self.assertIn(str(self.candidate),entries[0].read_text())
        self.assertEqual(m['state'],'READY_FOR_PROMOTION');u.rollback(m)
        self.assertEqual([p.read_text() for p in entries],before);self.assertEqual(keep.read_text(),'untouched');self.assertEqual(m['state'],'ROLLED_BACK')
    def test_second_launcher_failure_restores_first(self):
        m,entries,mf=self.promotion_fixture();before=[p.read_text() for p in entries];real=u.replace_text;calls=[]
        def flaky(path,text,mode):
            calls.append(path)
            if len(calls)==2:raise OSError('injected second-entry failure')
            real(path,text,mode)
        with patch.object(u.subprocess,'run',return_value=argparse.Namespace(returncode=1)), patch.object(u,'replace_text',side_effect=flaky):
            with self.assertRaises(OSError):u.promote(m,entries,self.base/'transaction',mf)
        self.assertEqual([p.read_text() for p in entries],before);self.assertEqual(json.loads((self.base/'transaction/transaction.json').read_text())['state'],'ROLLED_BACK')
    def test_new_tag_cannot_replace_existing_tag(self):
        m,entries,mf=self.promotion_fixture();before=[p.read_text() for p in entries]
        with patch.object(u.subprocess,'run',return_value=argparse.Namespace(returncode=0)):
            with self.assertRaisesRegex(ValueError,'tag already exists'):u.promote(m,entries,self.base/'transaction',mf)
        self.assertEqual([p.read_text() for p in entries],before)
    def test_atomic_desktop_replacement(self):
        p=self.base/'test.desktop';p.write_text('original');u.replace_text(p,'new',0o644);self.assertEqual(p.read_text(),'new');self.assertEqual([x.name for x in self.base.glob('test.desktop*')],['test.desktop'])
    def test_desktop_quoting_and_unsupported_characters(self):
        self.assertEqual(u.desktop_quote('/a path/x'),'"/a path/x"')
        for x in ['/x%f','/x\ny']:
            with self.assertRaises(ValueError):u.desktop_quote(x)


if __name__=='__main__':unittest.main()
