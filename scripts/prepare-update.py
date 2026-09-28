#!/usr/bin/env python3
"""Read-only update audit, isolated preparation and explicit reversible promotion.

Reports and candidates are PRIVATE. No downloader, installer automation, legal
acceptance, license copying, automatic production update or recursive deletion.
"""
import argparse
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid
sys.dont_write_bytecode = True
from pe_metadata import inspect_pe, sha256

REPO = Path(__file__).resolve().parents[1]
RULES = json.loads((REPO/'config/compatibility-rules.json').read_text())
STATES = {'CANDIDATE_CREATED','PREFLIGHT_FAILED','BASE_TESTING','BASE_PASS',
          'PLUGIN_TESTING','PLUGIN_PARTIAL','READY_FOR_PROMOTION','PROMOTED',
          'REJECTED','ROLLED_BACK'}
BASE_GATES = '''LAUNCH MODELING_VIEW LINE RECTANGLE PUSH_PULL SELECTION DELETE ORBIT PAN ZOOM
SAVE REOPEN GEOMETRY_PRESERVED UI_SCALE POINTER_ACCURACY HARDWARE_ACCELERATION VIEWPORT_QUALITY
NO_BUGSPLAT NO_LATE_CRASH NO_STALE_PROCESSES COLD_LAUNCH_1 COLD_LAUNCH_2 COLD_LAUNCH_3
FOCUS_LOSS_REPAINT FOCUS_REGAIN_REPAINT RIGHT_CLICK_POPUP_FIRST_PAINT NO_BLACK_CONTEXT_MENU_FLASH
MENU_FIRST_PAINT TOOLBAR_POPUP_PAINT PLUGIN_DIALOG_FIRST_PAINT PLUGIN_DIALOG_FOCUS_REPAINT
MAXIMIZE_RESTORE TOUCH_CRASH_CHECK TOUCHPAD_NAVIGATION NATIVE_VIEWPORT_RESOLUTION
PERFORMANCE_REVIEW FILE_FORMAT_REVIEW ROLLBACK_READY CONTENT_VERSION_REVIEW
COMPATIBILITY_REVIEW'''.split()
DESKTOP_GATES = '''APPS_LAUNCH DOCK_LAUNCH DOCK_FOCUS_EXISTING CORRECT_ICON
CORRECT_WINDOW_MATCHING NO_DUPLICATE_DOCK_ICON'''.split()


def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def overlap(a, b): return a == b or a.is_relative_to(b) or b.is_relative_to(a)
def windows(path): return any((p/'Windows').is_dir() and (p/'Users').is_dir() for p in (path,*path.parents))
def require(condition, message):
    if not condition: raise ValueError(message)


def path_guard(path, protected=(), new=False):
    path = path.expanduser().absolute()
    require(not any(p.is_symlink() for p in (path,*path.parents)), 'Symlink/alias path requires review')
    path = path.resolve()
    require(path != Path('/') and not windows(path), 'Refusing real Windows/root destination')
    require(not any(overlap(path, p.resolve()) for p in protected), 'Destination overlaps protected input/production/backup')
    require(not new or not path.exists(), 'Candidate/output already exists')
    return path


def save(path, value):
    # Callers guard paths. Replace one JSON file atomically and fsync it.
    temporary = path.with_name(path.name+'.new-'+uuid.uuid4().hex)
    with temporary.open('x') as stream:
        json.dump(value, stream, indent=2); stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, path)


def processes(root):
    markers = {('STEAM_COMPAT_DATA_PATH='+str(root/'compatdata')).encode(),
               ('WINEPREFIX='+str(root/'compatdata/pfx')).encode()}
    found=[]
    for p in Path('/proc').glob('[0-9]*/environ'):
        try:
            if markers.intersection(p.read_bytes().split(b'\0')): found.append(int(p.parent.name))
        except OSError: pass
    return found


def closed(root): require(not processes(root), 'Close this installation before changing or snapshotting it')


def file_manifest(root, runtime=False):
    """Hash files and symlink text without following directory links or caches."""
    result={}
    for base, dirs, names in os.walk(root, followlinks=False):
        base=Path(base)
        dirs[:] = sorted(d for d in dirs if d != '__pycache__' and not (runtime and d == 'var'))
        for name in sorted(set(dirs+names)):
            p=base/name; rel=p.relative_to(root).as_posix()
            if p.is_symlink(): result[rel]={'link':os.readlink(p)}
            elif p.is_file(): result[rel]={'bytes':p.stat().st_size,'sha256':sha256(p)}
    return result


def digest(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def version(meta):
    strings=meta.get('version_strings',{})
    values=set(strings.get('FileVersion',[])+strings.get('ProductVersion',[]))
    valid={x for x in values if re.fullmatch(r'\d+\.\d+\.\d+(?:\.\d+)?',x)}
    require(len(valid)==1, 'Unidentified or conflicting actual application build; audit StringFileInfo')
    return next(iter(valid))


def touch_decision(meta, runtime_name):
    t=RULES['touch']; h=meta['sha256']; present=t['export'] in meta.get('exports',[])
    if h==t['patched_sha256']:
        return {'state':'KNOWN_PATCHED','needed':'NO','native_support':'NO','action':'NO_OP'}
    if present:
        return {'state':'EXPORT_PRESENT_BEHAVIOR_UNVERIFIED','needed':'NO','native_support':'REQUIRES_BEHAVIOR_TEST','action':'TEST_NATIVE_NO_LEGACY_PATCH'}
    if h==t['stock_sha256'] and runtime_name==t['runtime']:
        return {'state':'KNOWN_STOCK_MISSING_EXPORT','needed':'YES','native_support':'NO','action':'EXACT_PATCH_ELIGIBLE'}
    return {'state':'UNKNOWN_MISSING_EXPORT','needed':'REQUIRES_AUDIT','native_support':'NO','action':'REQUIRES_REVIEW'}


def content_audit(root):
    categories={n:sum(p.is_file() and not p.is_symlink() for p in (root/n).rglob('*')) if (root/n).is_dir() else 0 for n in RULES['content_directories']}
    missing=[n for n,count in categories.items() if not count]
    if not (root/'Styles/StyleTemplate.skp').is_file(): missing.append('Styles/StyleTemplate.skp')
    files=file_manifest(root)
    require(not any('link' in v for v in files.values()), 'Content source symlinks require review')
    return {'files':files,'categories':categories,'missing':missing,'sha256':digest(files)}


def application_audit(root):
    require((root/'SketchUp.exe').is_file(), 'Missing SketchUp.exe')
    files=file_manifest(root); native={}
    require(not any('link' in v for v in files.values()), 'Application source symlinks require review')
    for rel in files:
        if Path(rel).suffix.lower() in ('.exe','.dll','.so'):
            info=inspect_pe(root/rel)
            native[rel]={k:v for k,v in info.items() if k not in ('exports',)}
    require(native['SketchUp.exe']['architecture']=='x86-64','Wrong architecture: SketchUp.exe')
    v=version(native['SketchUp.exe'])
    wrong=[n for n,m in native.items() if m['architecture']!='x86-64']
    # Native app .so/.dll payloads may change; unknown/inactive architectures need
    # explicit engineering rather than a filename-based automatic exemption.
    return {'version':v,'files':files,'native':native,'wrong_architecture':wrong,'sha256':digest(files)}


def runtime_audit(root):
    proton=[p for p in root.iterdir() if p.is_dir() and (p/'proton').is_file()]
    containers=[p for p in root.iterdir() if p.is_dir() and (p/'_v2-entry-point').is_file()]
    require(len(proton)==len(containers)==1,'Supply exactly one complete Proton and one container directory')
    pr,ct=proton[0],containers[0]
    require(not pr.is_symlink() and not ct.is_symlink(),'Runtime root aliases require review')
    needed=[pr/'files/bin/wine64',pr/'files/bin/wineserver',pr/'files/lib/wine/x86_64-windows/user32.dll',ct/'VERSIONS.txt']
    require(all(p.is_file() for p in needed),'Incomplete runtime')
    user32=inspect_pe(needed[2]);require(user32['architecture']=='x86-64','Wrong runtime user32 architecture')
    require(any(ct.glob('*_platform_*/files')),'Missing container platform files')
    files={}
    for directory in (pr,ct):
        for rel,meta in file_manifest(directory,runtime=True).items():
            if 'link' in meta:
                target=Path(meta['link'])
                # Standard absolute rootfs links are interpreted inside the
                # container. Links to another installation/Windows are refused.
                allowed=('/usr/','/lib/','/lib64/','/bin/','/sbin/','/etc/','/run/host/','/var/pressure-vessel/')
                require(not target.is_absolute() or str(target).startswith(allowed),'External runtime symlink requires review')
                if not target.is_absolute():
                    lexical=Path(os.path.abspath(directory/Path(rel).parent/target))
                    require(lexical.is_relative_to(root),'Runtime relative link escapes source root')
            files[directory.name+'/'+rel]=meta
    require(any('sniper' in p for p in files), 'Unidentified container payload')
    name=(pr/'version').read_text().strip() if (pr/'version').is_file() else pr.name
    return {'proton_directory':pr.name,'container_directory':ct.name,'proton_version':name,
            'container_version':(ct/'VERSIONS.txt').read_text().strip(),'user32':{k:v for k,v in user32.items() if k!='exports'},
            'touch':touch_decision(user32,pr.name),'files':files,'sha256':digest(files)}


def compare(old,new):
    return {k:('NEW' if k not in old else 'MISSING' if k not in new else 'UNCHANGED' if old[k]==new[k] else 'CHANGED') for k in sorted(old.keys()|new.keys())}


def classify(old,new,app_changed,runtime_changed,plugin_only=False):
    if plugin_only and not app_changed and not runtime_changed: return 'PLUGIN_ONLY_CHANGE'
    if not app_changed: return 'RUNTIME_ONLY_CHANGE' if runtime_changed else 'SAME_BUILD_REINSTALL'
    a=tuple(map(int,old.split('.')));b=tuple(map(int,new.split('.')))
    if a[0]!=b[0]: return 'MAJOR_UPDATE'
    if a[1]!=b[1]: return 'MINOR_UPDATE'
    return 'PATCH_UPDATE' if a!=b else 'UNKNOWN'


def rollback_verify(root):
    require((root/'manifest.json').is_file() and (root/'installation').is_dir(),'Independent rollback manifest/installation required')
    m=json.loads((root/'manifest.json').read_text());files=m.get('files',{});links=m.get('symlinks',{})
    require(files and any(x.endswith('SketchUp.exe') for x in files),'Rollback manifest is incomplete')
    for rel,info in files.items():
        p=root/'installation'/rel
        require(p.resolve().is_relative_to((root/'installation').resolve()),'Rollback file escapes snapshot')
        require(p.is_file() and sha256(p)==info['sha256'],'Rollback hash mismatch: '+rel)
    for rel,target in links.items():
        p=root/'installation'/rel
        require(p.is_symlink() and os.readlink(p)==target,'Rollback link mismatch: '+rel)
    return {'verified_files':len(files),'verified_links':len(links),'manifest_sha256':sha256(root/'manifest.json')}


def current_content(root):
    matches=list((root/'compatdata/pfx/drive_c/ProgramData/SketchUp').glob('*/SketchUp/Styles/StyleTemplate.skp'))
    require(len(matches)==1,'Current content root is ambiguous/missing')
    return matches[0].parents[1]


def settings(root):
    reg=root/'compatdata/pfx/user.reg';prefs=list((root/'compatdata/pfx/drive_c/users').glob('*/AppData/Local/SketchUp/*/SketchUp/PrivatePreferences.json'))
    text=reg.read_text(errors='replace') if reg.exists() else ''
    dpi=re.search(r'^"LogPixels"=dword:([a-fA-F0-9]+)$',text,re.M)
    return {'dpi':int(dpi[1],16) if dpi else 'DEFAULT_OR_UNSET','high_dpi_aware':'HIGHDPIAWARE' in text,
            'preferences':json.loads(prefs[0].read_text()).get('This Computer Only',{}).get('Preferences',{}) if len(prefs)==1 else 'UNSET_OR_AMBIGUOUS'}


def windows_mounts():
    roots=[]
    for line in Path('/proc/self/mountinfo').read_text().splitlines():
        token=line.split()[4]
        token=re.sub(r'\\([0-7]{3})',lambda m:chr(int(m[1],8)),token)
        p=Path(token)
        if (p/'Windows').is_dir() and (p/'Users').is_dir():roots.append(p)
    return sorted(set(roots))


def audit(args):
    current=args.current_root.resolve(strict=True);rollback=args.rollback_root.resolve(strict=True)
    sources=[args.app_source.resolve(strict=True),args.content_source.resolve(strict=True),args.runtime_source.resolve(strict=True)]
    require(all(p.is_dir() for p in sources),'Missing source directory')
    require(not overlap(current,rollback),'Rollback must be independent of production')
    protected=[p.resolve(strict=True) for p in getattr(args,'protect_root',[])]+windows_mounts()
    candidate=path_guard(args.candidate_root,[current,rollback,*sources,*protected],new=True)
    closed(current)
    old=application_audit(current/'app');new=application_audit(sources[0])
    old_content=content_audit(current_content(current));content=content_audit(sources[1])
    runtime=runtime_audit(sources[2]);old_runtime=runtime if sources[2]==current/'runtime' else runtime_audit(current/'runtime')
    backup=rollback_verify(rollback)
    app_diff=compare(old['files'],new['files']);content_diff=compare(old_content['files'],content['files']);runtime_diff=compare(old_runtime['files'],runtime['files'])
    changed=[p for p,s in app_diff.items() if s!='UNCHANGED']
    frameworks={name:[p for p in changed if re.search(pattern,p,re.I)] for name,pattern in
                {'QT':r'qt[56]','CEF':r'cef|chrome','RUBY':r'ruby','VC_RUNTIME':r'msvcp|vcruntime|concrt','UCRT':r'ucrt|api-ms-win-crt','GRAPHICS':r'opengl|vulkan|d3d|dxgi|angle|render|graphics'}.items()}
    review=[name+' changed' for name,paths in frameworks.items() if paths]
    if runtime['sha256']!=old_runtime['sha256']:review.append('Wine/container changed: all input, painting, graphics and native plugins')
    if not review:review=['Basic smoke tests for each promoted plugin; versions/hashes unchanged']
    known=new['version']==RULES['known_build']['version'] and new['native']['SketchUp.exe']['sha256']==RULES['known_build']['exe_sha256']
    needed=sum(v.get('bytes',0) for group in (new['files'],content['files'],runtime['files']) for v in group.values())+2*1024**3
    parent=candidate.parent
    while not parent.exists():parent=parent.parent
    free=shutil.disk_usage(parent).free;errors=[]
    if new['wrong_architecture']:errors.append('Wrong/unknown application native architecture: '+', '.join(new['wrong_architecture']))
    if content['missing']:errors.append('Missing content: '+', '.join(content['missing']))
    if free<needed:errors.append('Insufficient free disk space')
    msvcp=new['native'].get('msvcp140.dll')
    if not msvcp:errors.append('MSVCP140 supply/dependency audit required')
    ucrt=current/'compatdata/pfx/drive_c/windows/system32/ucrtbase.dll'
    return {'schema':1,'candidate_id':uuid.uuid4().hex,'created_utc':now(),'state':'PREFLIGHT_FAILED' if errors else 'CANDIDATE_CREATED',
      'root':str(candidate),'current_root':str(current),'rollback_root':str(rollback),'sources':dict(zip(('app','content','runtime'),map(str,sources))),
      'additional_protected':list(map(str,protected)), 'source_note':args.source_note,'application':new,'current_application':old,'runtime':runtime,'content':content,
      'content_source_version':args.content_version,'mixed_version_content':args.content_version!=new['version'],
      'current_version':old['version'],'candidate_version':new['version'],'classification':classify(old['version'],new['version'],bool(changed),runtime['sha256']!=old_runtime['sha256'],args.plugin_policy=='only'),
      'critical_file_diff':{n:{'status':app_diff[n],'current':old['native'].get(n),'candidate':new['native'].get(n)} for n in sorted(old['native'].keys()|new['native'].keys())},
      'diff':{'application':app_diff,'content':content_diff,'runtime':runtime_diff},'framework_changes':frameworks,
      'known_build':'KNOWN_METADATA' if known else 'REQUIRES_AUDIT',
      'known_build_fast_path':known and not changed and runtime['sha256']==old_runtime['sha256'] and not any(s!='UNCHANGED' for s in content_diff.values()),
      'old_fixes':{'MSVCP_REQUIRED':'NO' if msvcp and msvcp['architecture']=='x86-64' else 'YES_REQUIRES_LEGITIMATE_INPUT',
                   'UCRT_REQUIRED':'REQUIRES_DEPENDENCY_OR_FAILURE_EVIDENCE','DPI_REQUIRED':'REQUIRES_UI_TEST','PAINTING_REQUIRED':'REQUIRES_A_B_TEST','TOUCH':runtime['touch']},
      'current_ucrt':inspect_pe(ucrt) if ucrt.is_file() else None,'current_settings':settings(current),
      'plugin_policy':args.plugin_policy,'plugin_revalidation_plan':review,'prefix_strategy':'FRESH','fixes_applied':[],
      'graphics':'DETECT_AND_VALIDATE','dpi':'DEFAULT_UNTIL_REVIEW','rollback':backup,
      'disk':{'estimated_required_bytes':needed,'free_bytes':free},'preflight':{'status':'FAIL' if errors else 'PASS','errors':errors},
      'test_status':{},'history':[]}


def summary(m):
    return {'CANDIDATE':m['root'],'STATE':m['state'],'CURRENT_VERSION':m['current_version'],'NEW_VERSION':m['candidate_version'],
            'CLASSIFICATION':m['classification'],'RUNTIME':m['runtime']['proton_version'],'PREFLIGHT':m['preflight'],
            'FILES_CHANGED':sum(x!='UNCHANGED' for x in m['diff']['application'].values()),'FRAMEWORK_CHANGES':m['framework_changes'],
            'CONTENT_DIFFERENCES':sum(x!='UNCHANGED' for x in m['diff']['content'].values()),'KNOWN_FIXES_REQUIRING_REVIEW':m['old_fixes'],
            'PLUGIN_COMPATIBILITY_REVIEW_REQUIRED':m['plugin_revalidation_plan'],'BASE_TESTS':m['test_status'].get('base','NOT_TESTED'),
            'PLUGIN_TESTS':m['test_status'].get('plugins','NOT_TESTED'),'READY_FOR_PROMOTION':m['state']=='READY_FOR_PROMOTION'}


def private_report(path,m):
    protected=[Path(m[k]) for k in ('root','current_root','rollback_root')]+list(map(Path,m['sources'].values()))
    out=path_guard(path,protected,new=True);out.parent.mkdir(parents=True,exist_ok=True);save(out,m)


def create(m):
    require(m['preflight']['status']=='PASS','Preflight failed; no candidate created')
    root=path_guard(Path(m['root']),[Path(m['current_root']),Path(m['rollback_root']),*map(Path,m['sources'].values())],new=True)
    closed(Path(m['current_root']));root.mkdir(parents=True)
    for d in ('logs/updates','config','bin','compatdata','runtime/client'): (root/d).mkdir(parents=True,exist_ok=True)
    save(root/'candidate-manifest.json',m)
    protected=sorted(set([m['current_root'],m['rollback_root'],*m['sources'].values(),*m.get('additional_protected',[])]))
    for source in m['sources'].values():
        for ancestor in (Path(source),*Path(source).parents):
            if (ancestor/'Windows').is_dir() and (ancestor/'Users').is_dir(): protected.append(str(ancestor))
    require(not any(overlap(root,Path(p)) for p in protected),'Candidate overlaps protected mount')
    require(not any(':' in x for x in protected),'Colon in protected path is unsupported')
    save(root/'candidate-isolation.json',{'protected_readonly':protected})
    try:
        for label,relative in [('app','app'),('content','content')]:
            shutil.copytree(m['sources'][label],root/relative,symlinks=True)
            require(file_manifest(root/relative)==m['application' if label=='app' else 'content']['files'],'Copy hash mismatch')
        for directory in (m['runtime']['proton_directory'],m['runtime']['container_directory']):
            shutil.copytree(Path(m['sources']['runtime'])/directory,root/'runtime'/directory,symlinks=True,
                            ignore=shutil.ignore_patterns('var','__pycache__'))
        require(runtime_audit(root/'runtime')['files']==m['runtime']['files'],'Runtime copy hash mismatch')
        for name in ('prepare-update.py','pe_metadata.py','patch-wine-touch.py'):
            shutil.copy2(Path(__file__).with_name(name),root/'bin'/name)
        shutil.copy2(REPO/'config/compatibility-rules.json',root/'config/compatibility-rules.json')
        (root/'bin/launch-sketchup.py').write_text('#!/usr/bin/env python3\nimport runpy,sys\nfrom pathlib import Path\nr=Path(__file__).resolve().parents[1]\na=runpy.run_path(str(r/"bin/prepare-update.py"))\na["launch"](r, Path(sys.argv[1]) if len(sys.argv)>1 else None)\n')
        (root/'bin/launch-sketchup.py').chmod(0o755)
        # This entry stays inside the candidate, never installed or pinned.
        (root/'SketchUp-TEST.desktop').write_text('[Desktop Entry]\nType=Application\nName=SketchUp '+m['candidate_version']+' — TEST\nExec='+desktop_quote(str(root/'bin/launch-sketchup.py'))+' %f\nTerminal=false\nStartupWMClass=steam_app_0\n')
        m['history'].append({'utc':now(),'action':'CREATE','source_copies_verified':True})
    except Exception as e:
        m['state']='PREFLIGHT_FAILED';m['preflight']={'status':'FAIL','errors':[str(e)]};save(root/'candidate-manifest.json',m);raise
    save(root/'candidate-manifest.json',m)
    return m


def load(root):
    root=root.resolve(strict=True);p=root/'candidate-manifest.json';m=json.loads(p.read_text())
    require(m.get('schema')==1 and m.get('root')==str(root) and m.get('state') in STATES,'Invalid/relocated candidate manifest')
    path_guard(root,[Path(m['current_root']),Path(m['rollback_root']),*map(Path,m['sources'].values())])
    return m


def store(m): save(Path(m['root'])/'candidate-manifest.json',m)
def stage(m,state):
    m['history'].append({'utc':now(),'from':m['state'],'to':state});m['state']=state;store(m)


def command_env(m):
    root=Path(m['root']);runtime=root/'runtime';env={k:v for k,v in os.environ.items() if k in ('DISPLAY','XAUTHORITY','XDG_RUNTIME_DIR','DBUS_SESSION_BUS_ADDRESS','LANG','PATH','HOME','USER','LOGNAME')}
    protected=json.loads((root/'candidate-isolation.json').read_text())['protected_readonly']
    env.update(STEAM_COMPAT_DATA_PATH=str(root/'compatdata'),STEAM_COMPAT_CLIENT_INSTALL_PATH=str(runtime/'client'),
      STEAM_COMPAT_INSTALL_PATH=str(root/'app'),STEAM_COMPAT_LIBRARY_PATHS=str(root),STEAM_COMPAT_MOUNTS=str(root),
      STEAM_COMPAT_TOOL_PATHS=str(runtime/m['runtime']['proton_directory'])+':'+str(runtime/m['runtime']['container_directory']),
      UMU_ID='umu-sketchup',STEAM_COMPAT_PROTON='1',STEAM_COMPAT_APP_ID='0',SteamAppId='0',SteamGameId='0',PROTON_ENABLE_WAYLAND='0',
      PROTON_LOG='1',PROTON_LOG_DIR=str(root/'logs'),WINEDEBUG='-all,err+all',PRESSURE_VESSEL_FILESYSTEMS_RO=':'.join(protected))
    if m.get('known_settings'): env.update(SU_CEF_DISABLE_GPU='1',PROTON_USE_WINED3D='0',FONTCONFIG_FILE=str(root/'config/fontconfig.conf'))
    return env


def runtime_command(m, executable, tail=()):
    root=Path(m['root']);rt=root/'runtime'
    return [str(rt/m['runtime']['container_directory']/'_v2-entry-point'),'--verb=run','--','/usr/bin/python3',
            str(root/'bin/prepare-update.py'),'runtime-entry','--candidate-root',str(root),'--executable',executable,*tail]


def initialize(m,apply_touch=False):
    root=Path(m['root']);closed(root);require(m['state']=='CANDIDATE_CREATED','Initialize only a new candidate')
    require(not (root/'compatdata/pfx').exists(),'Prefix already exists; review partial initialization instead of merging')
    require(application_audit(root/'app')['files']==m['application']['files'],'Application changed since copy')
    require(content_audit(root/'content')['files']==m['content']['files'],'Content changed since copy')
    t=runtime_audit(root/'runtime')['touch'];user32=root/'runtime'/m['runtime']['proton_directory']/'files/lib/wine/x86_64-windows/user32.dll'
    if apply_touch:
        require(t['action'] in ('EXACT_PATCH_ELIGIBLE','NO_OP'),'Touch patch not eligible')
        if t['action']=='EXACT_PATCH_ELIGIBLE':
            subprocess.run([sys.executable,str(Path(__file__).with_name('patch-wine-touch.py')),str(user32)],check=True)
            m['fixes_applied'].append('EXACT_TOUCH_ALIAS')
    require(t['action']!='REQUIRES_REVIEW','Unknown missing touch export: investigate before launch')
    if t['action']=='EXACT_PATCH_ELIGIBLE': require(apply_touch,'Known missing touch export; explicitly request exact patch or use another candidate')
    store(m)
    with (root/'logs/updates/prefix-init.log').open('w') as out:
        subprocess.run(runtime_command(m,'C:\\windows\\system32\\cmd.exe',['--runtime-argument','/c','--runtime-argument','exit','--runtime-argument','0']),env=command_env(m),stdout=out,stderr=subprocess.STDOUT,check=True,timeout=180)
    closed(root)
    require((root/'compatdata/pfx/user.reg').is_file(),'Fresh prefix initialization failed')
    year=2000+int(m['candidate_version'].split('.')[0]);require(2020<=year<=2099,'Unknown content year mapping')
    dest=root/f'compatdata/pfx/drive_c/ProgramData/SketchUp/SketchUp {year}/SketchUp'
    dest.parent.mkdir(parents=True,exist_ok=True);require(not dest.exists(),'Unexpected existing content')
    shutil.copytree(root/'content',dest)
    # Remove only freshly generated drive links, not Windows or user files.
    drives=root/'compatdata/pfx/dosdevices'
    for p in drives.iterdir():
        if p.is_symlink() and p.name not in ('c:','z:'): p.unlink()
    # Proton may generate host user-folder links; redirect candidate users to
    # empty local folders. No data behind these links is touched or copied.
    for p in (root/'compatdata/pfx/drive_c/users').rglob('*'):
        if p.is_symlink() and not p.resolve().is_relative_to(root):
            p.unlink();p.mkdir()
    m['initialized']=True;stage(m,'BASE_TESTING');return m


def configure_known(m, ucrt, evidence):
    """Explicit reinstall recipe; never an automatic unknown-build fallback."""
    root=Path(m['root']);closed(root)
    require(m['state']=='BASE_TESTING' and m.get('initialized'),'Configure only before base validation')
    require(m['known_build']=='KNOWN_METADATA' and m['runtime']['proton_directory']=='GE-Proton10-25' and m.get('known_build_fast_path'), 'Recipe requires the exact unchanged known app/content/runtime; changed frameworks need narrower engineering')
    require(evidence.get('candidate_id')==m['candidate_id'] and evidence.get('reviewer') and evidence.get('evidence'), 'Reviewed compatibility evidence required')
    required=('UCRT_REQUIRED','DPI_REQUIRED','CLASSIC_MSAA8_REQUIRED','PAINTING_REQUIRED','CEF_GPU_WORKAROUND_REQUIRED','FONT_FILTER_REQUIRED')
    require(all(evidence.get(k)=='YES' for k in required),'Recipe needs a reasoned YES for every applied setting; use narrower manual engineering otherwise')
    meta=inspect_pe(ucrt)
    require(meta['architecture']=='x86-64' and meta['sha256']=='51cbbde17a768930300236facd9738f54b7801e6715771ff8af90bfbe3fad44f','This recipe requires the exact legitimate tested UCRT')
    require(evidence.get('runtime_provenance'),'Document the legitimate UCRT package/source and hash')
    for dll in [root/'runtime/GE-Proton10-25/files/lib/wine/x86_64-windows/user32.dll',root/'compatdata/pfx/drive_c/windows/system32/user32.dll']:
        require(sha256(dll)==RULES['touch']['patched_sha256'],'Known touch patch must be present in runtime and fresh prefix')
    require(inspect_pe(root/'app/msvcp140.dll')['architecture']=='x86-64','Wrong MSVCP architecture')
    require(not (root/'logs/updates/configuration-before.json').exists(),'A previous configuration attempt exists; review before repeating')
    require(not list((root/'compatdata/pfx/drive_c/users').glob('*/AppData/Local/SketchUp/*/SketchUp/PrivatePreferences.json')),'Existing preferences need a reviewed narrow edit')
    dst=root/'compatdata/pfx/drive_c/windows/system32';shutil.copy2(ucrt,dst/'ucrtbase.dll');shutil.copy2(root/'app/msvcp140.dll',dst/'msvcp140.dll')
    reg=root/'compatdata/pfx/user.reg';text=reg.read_text()
    save(root/'logs/updates/configuration-before.json',{'registry':text,'evidence':evidence})
    def value(section,name,data):
        nonlocal text
        marker='['+section.replace('\\','\\\\')+']';start=text.find(marker)
        if start<0:text+='\n'+marker+'\n"'+name+'"='+data+'\n';return
        end=text.find('\n[',start+1);end=len(text) if end<0 else end
        block=re.sub(r'^"'+re.escape(name)+r'"=.*\n?','',text[start:end],flags=re.M)
        text=text[:start]+block+'\n"'+name+'"='+data+'\n'+text[end:]
    value('Control Panel\\Desktop','LogPixels','dword:000000c0')
    value('Software\\Wine\\AppDefaults\\SketchUp.exe','Version','"win10"')
    value('Software\\Wine\\DllOverrides','ucrtbase','"native,builtin"')
    value('Software\\Wine\\X11 Driver','ClientSideGraphics','"N"')
    marker='[Software\\\\Microsoft\\\\Windows NT\\\\CurrentVersion\\\\AppCompatFlags\\\\Layers]'
    require(marker not in text,'Unexpected existing DPI layers; review before merging')
    text+='\n'+marker+'\n@="HIGHDPIAWARE"\n';reg.write_text(text)
    prefs=root/'compatdata/pfx/drive_c/users/steamuser/AppData/Local/SketchUp/SketchUp 2026/SketchUp/PrivatePreferences.json'
    require(not prefs.exists(),'Existing preferences need a reviewed narrow edit')
    prefs.parent.mkdir(parents=True,exist_ok=True)
    save(prefs,{'This Computer Only':{'Preferences':{'UseNewRenderer':False,'TryNewRenderer':False,'CountOfNewRenderersOnProbation':0,'AAMethod':8,'UseFastFeedback':False,'ValidateGraphicsCardPrefs':True}}})
    (root/'config/fontconfig.conf').write_text('<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd"><fontconfig><include ignore_missing="yes">/etc/fonts/fonts.conf</include><selectfont><rejectfont><glob>/usr/share/fonts/noto-emoji/NotoColorEmoji.ttf</glob><glob>/run/host/fonts/truetype/noto/NotoColorEmoji.ttf</glob><glob>/run/host/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf</glob></rejectfont></selectfont></fontconfig>\n')
    for name in ('runtime-exec.py','popup-present.c','build-popup-helper.py'):
        shutil.copy2(Path(__file__).with_name(name),root/'bin'/name)
    subprocess.run([sys.executable,str(root/'bin/build-popup-helper.py'),'--root',str(root)],check=True)
    m['known_settings']=True;m['graphics']='Classic OpenGL / MSAA 8; TEST REQUIRED';m['dpi']='192 / HIGHDPIAWARE; TEST REQUIRED'
    m['fixes_applied']+=list(required);m['configuration_evidence']=evidence;m['old_fixes'].update(UCRT_REQUIRED='YES',DPI_REQUIRED='YES',PAINTING_REQUIRED='YES');store(m)
    return summary(m)


def runtime_entry(m,exe,args):
    root=Path(m['root']);protected=json.loads((root/'candidate-isolation.json').read_text())['protected_readonly']
    result={p:bool(os.statvfs(p).f_flag & os.ST_RDONLY) for p in protected}
    save(root/'logs/updates/isolation-enforced.json',result);require(result and all(result.values()),'Protected path writable inside container')
    proton=root/'runtime'/m['runtime']['proton_directory']/'proton'
    env=os.environ.copy()
    if (root/'config/popup-present.json').exists():
        import runpy
        env=runpy.run_path(str(root/'bin/runtime-exec.py'))['helper_environment'](root,env)
    os.execve(proton,[str(proton),'run',exe,*args],env)


def launch(root,model=None):
    m=load(root);require(m.get('initialized') and m['state'] in ('BASE_TESTING','BASE_PASS','PLUGIN_TESTING','PLUGIN_PARTIAL','READY_FOR_PROMOTION','PROMOTED'),'Candidate is not initialized/testable')
    app=Path(m['root'])/'app/SketchUp.exe';require(sha256(app)==m['application']['files']['SketchUp.exe']['sha256'],'Application hash changed; re-audit')
    unit='aag-sketchup-update-'+m['candidate_id'][:12]+'.service'
    runtime_dir=Path(os.environ.get('XDG_RUNTIME_DIR','/run/user/'+str(os.getuid())))
    with (runtime_dir/(unit+'.lock')).open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        pids=processes(root)
        if pids:
            for row in subprocess.check_output(['wmctrl','-lp'],text=True).splitlines():
                fields=row.split(None,4)
                if len(fields)>3 and fields[2].isdigit() and int(fields[2]) in pids:
                    subprocess.run(['wmctrl','-ia',fields[0]],check=True)
            return
        require(subprocess.run(['systemctl','--user','is-active','--quiet',unit]).returncode!=0,'Candidate unit still active')
        tail=[]
        if model:
            model=model.resolve(strict=True);tail=['--runtime-argument','Z:'+str(model).replace('/',chr(92))]
        cmd=['systemd-run','--user','--collect','--unit='+unit,'--property=ExitType=cgroup','--property=KillMode=control-group',
             '--property=TimeoutStopSec=8','--property=Restart=no','--property=RuntimeMaxSec=infinity',
             '--property=StandardOutput=append:'+str(root/'logs/updates/console.log'),'--property=StandardError=append:'+str(root/'logs/updates/console.log')]
        cmd+=['--setenv='+k+'='+v for k,v in command_env(m).items()]
        cmd+=['/usr/bin/env','-u','WAYLAND_DISPLAY','-u','WINEPREFIX','-u','LD_PRELOAD','-u','LD_LIBRARY_PATH','-u','QT_SCALE_FACTOR','-u','SU_CEF_DBG_PORT']
        subprocess.run(cmd+runtime_command(m,'Z:'+str(app).replace('/',chr(92)),tail),check=True)


def regression_template(m):
    return {'candidate_id':m['candidate_id'],'version':m['candidate_version'],'reviewer':'','evidence':[],
            'base_gates':dict.fromkeys(BASE_GATES,'NOT_TESTED'),'post_promotion_gates':dict.fromkeys(DESKTOP_GATES,'NOT_TESTED'),
            'plugins':[],'plugin_production_regression':'NOT_TESTED','backward_file_compatibility':'UNKNOWN',
            'plugin_regression_accepted_by_user':False,'known_limitations':[],
            'notes':'Manual PASS needs observed evidence. Template creation does not validate GUI behavior.'}


def checked_evidence(m,e,gates,section):
    require(e.get('candidate_id')==m['candidate_id'] and e.get('version')==m['candidate_version'],'Evidence belongs to another candidate')
    require(e.get('reviewer') and e.get('evidence'),'Human review and local evidence references required')
    require(all(e.get(section,{}).get(g)=='PASS' for g in gates),'Required '+section+' have not all passed')


def fingerprint(root):
    # Full prefix captures plugin/settings changes. Logs/container caches vary.
    result={}
    for name in ('app','content','runtime','config','bin','compatdata'):
        result[name]=digest(file_manifest(root/name,runtime=(name=='runtime')))
    return result


def validate(m,e,phase):
    root=Path(m['root']);closed(root)
    require(m.get('initialized'),'Candidate prefix is not initialized')
    if phase=='base':
        require(m['state']=='BASE_TESTING','Base validation must precede plugins')
        checked_evidence(m,e,BASE_GATES,'base_gates')
        require(e.get('backward_file_compatibility') in ('YES','NO','UNKNOWN'),'File format compatibility must be recorded')
        m['base_evidence']=e;m['test_status']['base']='PASS';stage(m,'BASE_PASS')
    elif phase=='plugins':
        require(m['state'] in ('BASE_PASS','PLUGIN_TESTING','PLUGIN_PARTIAL'),'Base tests must pass first')
        checked_evidence(m,e,BASE_GATES,'base_gates')
        rows=e.get('plugins',[])
        require(rows or m['plugin_policy']=='none','Plugin matrix required')
        require(all(p.get('result') in ('PASS','PARTIAL','FAIL','NOT_TESTED','UPDATE_REQUIRED','USER_ACTION_DEFERRED') and p.get('name') and p.get('evidence') for p in rows),'Incomplete plugin matrix')
        installed=[p for p in rows if p.get('installed')]
        require(all(p['result'] in ('PASS','PARTIAL') for p in installed),'Untested/failing plugin remains installed')
        require(not installed or e.get('plugin_production_regression')=='PASS','Combined plugin regression required')
        if any(p['result'] in ('FAIL','NOT_TESTED','UPDATE_REQUIRED') for p in rows):
            require(e.get('plugin_regression_accepted_by_user') is True,'User must understand any plugin regression before replacement')
        m['plugin_evidence']=e;m['test_status']['plugins']='PARTIAL' if any(p['result']!='PASS' for p in rows) else 'PASS'
        stage(m,'PLUGIN_PARTIAL' if m['test_status']['plugins']=='PARTIAL' else 'PLUGIN_TESTING')
    else:
        require(m['state'] in ('BASE_PASS','PLUGIN_TESTING','PLUGIN_PARTIAL'),'Candidate is not ready for acceptance review')
        require(m['plugin_policy']=='none' or 'plugin_evidence' in m,'Plugin validation missing')
        rollback_verify(Path(m['rollback_root']))
        require(not application_audit(root/'app')['wrong_architecture'],'Application architecture changed')
        require(not content_audit(root/'content')['missing'],'Content no longer complete')
        # Record the entire accepted candidate after it is closed. Any subsequent
        # binary/prefix/settings/plugin change invalidates promotion.
        m['accepted_fingerprint']=fingerprint(root);m['accepted_utc']=now();stage(m,'READY_FOR_PROMOTION')
    return m


def desktop_quote(value):
    require(not any(c in value for c in ('\n','\r','%')),'Unsupported desktop path character')
    return '"'+re.sub(r'([\\"`$])',r'\\\1',value)+'"'


def promote(m,entries,transaction,metadata):
    root=Path(m['root']);current=Path(m['current_root']);closed(root);closed(current)
    require(m['state']=='READY_FOR_PROMOTION' and not m.get('promotion'),'Candidate not ready or transaction already started')
    require(fingerprint(root)==m['accepted_fingerprint'],'Accepted candidate changed; repeat validation')
    rollback_verify(Path(m['rollback_root']))
    meta=json.loads(metadata.read_text())
    require(meta.get('candidate_id')==m['candidate_id'] and meta.get('version')==m['candidate_version'],'Metadata target mismatch')
    require(meta.get('backward_file_warning_reviewed') is True, 'File format rollback warning must be reviewed')
    require(meta.get('plugin_changes_reviewed_by_user') is True, 'Production plugin scope/change review is required')
    required=['README.md','artifacts/current-golden-baseline.json','docs/GOLDEN-HISTORY.md','docs/PLUGINS.md','docs/TEST-MATRIX.md',meta.get('update_report','')]
    require(meta.get('new_tag') and meta.get('rollback_root')==m['rollback_root'] and all(n in meta.get('reviewed_files',{}) for n in required),'Canonical metadata/release plan incomplete')
    repo=Path(meta['repository']).resolve(strict=True)
    for name,h in meta['reviewed_files'].items():
        p=repo/name;require(p.resolve().is_relative_to(repo) and p.is_file() and sha256(p)==h,'Reviewed metadata changed')
    require(subprocess.run(['git','-C',str(repo),'rev-parse','--verify','refs/tags/'+meta['new_tag']],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode!=0,'Golden tag already exists; never move it')
    protected=[root,current,Path(m['rollback_root']),*map(Path,m['sources'].values())]
    tx=path_guard(transaction,protected,new=True)
    require(entries and len(set(map(str,entries)))==len(entries),'Explicit distinct desktop entries required')
    prepared=[]
    for entry in entries:
        entry=path_guard(entry,protected);require(entry.is_file() and entry.suffix=='.desktop','Expected regular existing desktop entry')
        text=entry.read_text();old_exec='Exec='+desktop_quote(str(current/'bin/launch-sketchup.py'))+' %f'
        require(old_exec in text.splitlines(),'Desktop launcher does not target current Golden exactly')
        icon=root/'config/icons/sketchup.png';require(icon.is_file(),'Candidate icon must be prepared and visually validated')
        new=text.replace(old_exec,'Exec='+desktop_quote(str(root/'bin/launch-sketchup.py'))+' %f')
        new=re.sub(r'^Icon=.*$', 'Icon='+str(icon),new,flags=re.M)
        new=re.sub(r'^Name=.*$', 'Name=SketchUp '+str(2000+int(m['candidate_version'].split('.')[0])),new,flags=re.M)
        wmclass=meta.get('startup_wm_class')
        require(wmclass and re.fullmatch(r'[A-Za-z0-9_.-]+',wmclass),'Reviewed actual StartupWMClass required')
        new=re.sub(r'^StartupWMClass=.*$', 'StartupWMClass='+wmclass,new,flags=re.M)
        require('StartupWMClass='+wmclass in new.splitlines(),'Desktop entry lacks StartupWMClass')
        prepared.append({'path':str(entry),'before':text,'after':new,'mode':entry.stat().st_mode & 0o777})
    tx.mkdir(parents=True);journal={'schema':1,'candidate':str(root),'current':str(current),'state':'PREPARED','entries':prepared,'metadata':meta,'utc':now()};save(tx/'transaction.json',journal)
    try:
        for item in prepared: replace_text(Path(item['path']),item['after'],item['mode'])
        journal['state']='AWAITING_POST_PROMOTION_GUI';save(tx/'transaction.json',journal)
        m['promotion']=str(tx);store(m)
    except Exception:
        for item in prepared: replace_text(Path(item['path']),item['before'],item['mode'])
        journal['state']='ROLLED_BACK';save(tx/'transaction.json',journal);raise
    return {'state':'AWAITING_POST_PROMOTION_GUI','transaction':str(tx),'old_golden_retained':True,'tag_created':False}


def replace_text(path,text,mode):
    tmp=path.with_name(path.name+'.aag-new-'+uuid.uuid4().hex)
    with tmp.open('x') as f:f.write(text);f.flush();os.fsync(f.fileno())
    tmp.chmod(mode);os.replace(tmp,path)


def finish(m,e):
    require(m.get('promotion') and m['state']=='READY_FOR_PROMOTION','No pending promotion')
    checked_evidence(m,e,DESKTOP_GATES,'post_promotion_gates');closed(Path(m['root']))
    tx=Path(m['promotion']);j=json.loads((tx/'transaction.json').read_text())
    require(all(Path(x['path']).read_text()==x['after'] for x in j['entries']),'Launcher changed during promotion')
    j['state']='PROMOTED';j['post_promotion_evidence']=e;save(tx/'transaction.json',j)
    m['post_promotion_evidence']=e;stage(m,'PROMOTED');return summary(m)


def rollback(m):
    require(m.get('promotion'),'No promotion to reverse')
    root=Path(m['root']);closed(root);closed(Path(m['current_root']))
    tx=Path(m['promotion']);j=json.loads((tx/'transaction.json').read_text())
    require(j['candidate']==str(root) and j['state'] in ('AWAITING_POST_PROMOTION_GUI','PROMOTED'),'Invalid rollback transaction')
    for x in j['entries']:
        p=path_guard(Path(x['path']),[root,Path(m['current_root']),Path(m['rollback_root'])]);require(p.read_text()==x['after'],'Launcher modified since promotion; review before rollback')
    for x in j['entries']: replace_text(Path(x['path']),x['before'],x['mode'])
    j['state']='ROLLED_BACK';save(tx/'transaction.json',j);stage(m,'ROLLED_BACK');return summary(m)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('operation',choices=['audit','create','initialize','configure-known','status','template','validate','launch','runtime-entry','reject','cleanup-plan','promote','finish','rollback'])
    p.add_argument('--candidate-root',type=Path,required=True)
    for n in ('current-root','app-source','content-source','runtime-source','rollback-root','report','evidence','model','transaction','metadata','ucrt-source'):p.add_argument('--'+n,type=Path)
    p.add_argument('--protect-root',type=Path,action='append',default=[])
    p.add_argument('--content-version');p.add_argument('--source-note');p.add_argument('--plugin-policy',choices=['none','revalidate','only'],default='revalidate')
    p.add_argument('--dry-run',action='store_true');p.add_argument('--apply-known-touch',action='store_true');p.add_argument('--phase',choices=['base','plugins','ready'])
    p.add_argument('--reason');p.add_argument('--desktop-entry',type=Path,action='append');p.add_argument('--executable');p.add_argument('--runtime-argument',action='append',default=[])
    a=p.parse_args()
    require(not a.dry_run or a.operation in ('audit','create','cleanup-plan','status'), '--dry-run is not supported for this mutation; refusing rather than ignoring it')
    if a.operation in ('audit','create'):
        require(all(getattr(a,n) for n in ('current_root','app_source','content_source','runtime_source','rollback_root','content_version','source_note')),'Explicit current/source/content version/provenance/rollback arguments required')
        m=audit(a)
        if a.report: private_report(a.report,m)
        if a.operation=='create' and not a.dry_run: m=create(m)
        print(json.dumps(summary(m),indent=2));return 0 if m['preflight']['status']=='PASS' else 2
    operation_lock=None
    if a.operation not in ('status','template','launch','runtime-entry','cleanup-plan'):
        load(a.candidate_root)  # validate destination before creating the lock
        operation_lock=(a.candidate_root/'.update.lock').open('w')
        fcntl.flock(operation_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    m=load(a.candidate_root)
    if a.operation=='status':result=summary(m)
    elif a.operation=='template':result=regression_template(m)
    elif a.operation=='initialize':
        try:result=summary(initialize(m,a.apply_known_touch))
        except Exception as error:
            m['initialization_failure']=str(error);stage(m,'PREFLIGHT_FAILED');raise
    elif a.operation=='configure-known':
        require(a.ucrt_source and a.evidence,'Explicit UCRT source and review evidence required');result=configure_known(m,a.ucrt_source,json.loads(a.evidence.read_text()))
    elif a.operation=='launch':launch(a.candidate_root,a.model);return 0
    elif a.operation=='runtime-entry':runtime_entry(m,a.executable,a.runtime_argument);return 0
    elif a.operation=='validate':
        require(a.phase,'Validation phase required');e=json.loads(a.evidence.read_text()) if a.evidence else {};result=summary(validate(m,e,a.phase))
    elif a.operation=='reject':
        require(a.reason and m['state'] not in ('PROMOTED','ROLLED_BACK') and not m.get('promotion'),'Rejection requires reason and no active promotion');closed(a.candidate_root)
        m['rejection']={'reason':a.reason,'stage':m['state'],'production_impact':'NONE','cleanup_status':'RETAINED'};stage(m,'REJECTED');result=summary(m)
    elif a.operation=='cleanup-plan':
        require(m['state']=='REJECTED','Only a rejected candidate can be proposed for cleanup');closed(a.candidate_root)
        result={'candidate':m['root'],'would_remove':[m['root']],'preserve_first':['candidate-manifest.json','logs/updates','private crash evidence'],'deleted':False,'requires':'Fresh exact-path deletion authorization and final launcher/backup/reference checks; this tool never deletes a candidate'}
    elif a.operation=='promote':
        require(a.transaction and a.metadata,'Transaction and metadata review files required');result=promote(m,a.desktop_entry,a.transaction,a.metadata)
    elif a.operation=='finish':require(a.evidence,'Post-promotion evidence required');result=finish(m,json.loads(a.evidence.read_text()))
    else:result=rollback(m)
    print(json.dumps(result,indent=2));return 0


if __name__=='__main__':
    try:sys.exit(main())
    except (OSError,ValueError,KeyError,subprocess.SubprocessError) as e:
        print('REFUSED: '+str(e),file=sys.stderr);sys.exit(2)
