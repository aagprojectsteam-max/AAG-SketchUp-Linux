#!/usr/bin/env python3
"""Repair the demonstrated GNOME US/Hebrew -> Xwayland map mismatch once.

This changes the current Xwayland display, not GNOME's saved input sources.
It reads no typed input and starts no background service.
"""
import ast
import ctypes
import ctypes.util
import json
import os
from pathlib import Path
import re
import subprocess


def run(argv, **kwargs):
    return subprocess.run(argv, check=True, capture_output=True, text=True,
                          timeout=10, **kwargs).stdout.strip()


def setting(name):
    text = run(['gsettings', 'get', 'org.gnome.desktop.input-sources', name])
    # GVariant annotates an empty array (for example @as [] or @a(ss) []).
    text = re.sub(r'^@[A-Za-z()]+\s+', '', text)
    return ast.literal_eval(text)


def source_config(sources, model, options):
    # The validated repair is deliberately limited to these two existing sources.
    if sources not in ([('xkb', 'us'), ('xkb', 'il')], [('xkb', 'il'), ('xkb', 'us')]):
        return None
    if not isinstance(model, str) or (model and not re.fullmatch(r'[A-Za-z0-9_+()-]{1,80}', model)):
        raise ValueError('Unsupported GNOME keyboard model')
    if not isinstance(options, list) or any(not isinstance(s, str) or
            not re.fullmatch(r'[A-Za-z0-9_:()+-]{1,100}', s) for s in options):
        raise ValueError('Unsupported GNOME XKB options')
    return {'layouts': [s[1] for s in sources], 'model': model, 'options': options}


def rules(text):
    data = dict(line.split(':', 1) for line in text.splitlines() if ':' in line)
    return {k.strip(): v.strip() for k, v in data.items()}


def action(config, mapping, properties):
    if config is None:
        return 'NOT_APPLICABLE'
    if 'hebrew_' in mapping and 'English (US)' in mapping:
        return 'ALREADY_PRESENT'
    if (properties.get('layout') == 'us' and not properties.get('variant') and
            'hebrew_' not in mapping and 'name[group1]="English(US)"' in mapping.replace(' ', '')
            and 'name[group2]' not in mapping.replace(' ', '')):
        return 'REPAIR_US_ONLY_MAP'
    return 'UNSUPPORTED_MAP_REVIEW_REQUIRED'


class XkbState(ctypes.Structure):
    _fields_ = [('group', ctypes.c_ubyte), ('locked_group', ctypes.c_ubyte),
                ('base_group', ctypes.c_ushort), ('latched_group', ctypes.c_ushort),
                ('mods', ctypes.c_ubyte), ('base_mods', ctypes.c_ubyte),
                ('latched_mods', ctypes.c_ubyte), ('locked_mods', ctypes.c_ubyte),
                ('compat_state', ctypes.c_ubyte), ('grab_mods', ctypes.c_ubyte),
                ('compat_grab_mods', ctypes.c_ubyte), ('lookup_mods', ctypes.c_ubyte),
                ('compat_lookup_mods', ctypes.c_ubyte), ('ptr_buttons', ctypes.c_ushort)]


def lock_group(display, group):
    lib = ctypes.CDLL(ctypes.util.find_library('X11'))
    lib.XOpenDisplay.argtypes = [ctypes.c_char_p]; lib.XOpenDisplay.restype = ctypes.c_void_p
    lib.XCloseDisplay.argtypes = [ctypes.c_void_p]
    lib.XkbLockGroup.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint]
    lib.XkbGetState.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.POINTER(XkbState)]
    lib.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]
    connection = lib.XOpenDisplay(display.encode())
    if not connection:
        raise RuntimeError('Cannot open the current Xwayland display')
    try:
        if not lib.XkbLockGroup(connection, 0x100, group):
            raise RuntimeError('XKB rejected the selected input group')
        lib.XSync(connection, 0)
        state = XkbState()
        if lib.XkbGetState(connection, 0x100, ctypes.byref(state)) or state.group != group:
            raise RuntimeError('The selected XKB group was not applied')
    finally:
        lib.XCloseDisplay(connection)


def set_command(display, model, layouts, options, rules_name=None, variant=None):
    cmd = ['setxkbmap', '-display', display, '-model', model, '-layout', layouts]
    if rules_name:
        cmd += ['-rules', rules_name]
    cmd += ['-variant', variant or '', '-option', '']
    for option in options:
        cmd += ['-option', option]
    return cmd


def prepare(log, environ=None):
    env = os.environ if environ is None else environ
    if env.get('XDG_SESSION_TYPE') != 'wayland' or 'GNOME' not in env.get('XDG_CURRENT_DESKTOP', ''):
        return {'status': 'NOT_APPLICABLE', 'reason': 'outside GNOME Wayland'}
    display = env.get('DISPLAY', '')
    if not re.fullmatch(r':\d+(?:\.\d+)?', display):
        return {'status': 'NOT_APPLICABLE', 'reason': 'no local X display'}
    # Never select a nested or arbitrary X server on behalf of the caller.
    extension = run(['xdpyinfo', '-display', display, '-queryExtensions'])
    if 'XWAYLAND' not in extension:
        return {'status': 'NOT_APPLICABLE', 'reason': 'current display is not Xwayland'}
    config = source_config(setting('sources'), setting('xkb-model'), setting('xkb-options'))
    if config is None:
        return {'status': 'NOT_APPLICABLE', 'reason': 'input sources outside validated US/Hebrew case'}
    mapping = run(['xkbcomp', '-xkb', display, '-'])
    previous = rules(run(['setxkbmap', '-display', display, '-query']))
    decision = action(config, mapping, previous)
    if decision != 'REPAIR_US_ONLY_MAP':
        if decision == 'UNSUPPORTED_MAP_REVIEW_REQUIRED':
            raise ValueError('Xwayland lacks the configured Hebrew map; custom map needs review')
        return {'status': decision, 'display': display}
    engine_groups = {'xkb:us::eng': config['layouts'].index('us'),
                     'xkb:il::heb': config['layouts'].index('il')}
    engine = run(['ibus', 'engine'])
    if engine not in engine_groups:
        raise ValueError('Cannot establish the active GNOME US/Hebrew source')
    log = Path(log)
    backup = log/'xwayland-before.xkb'
    with backup.open('x') as stream:
        os.chmod(backup, 0o600)
        stream.write(mapping + '\n')
    metadata = log/'xwayland-before.json'
    with metadata.open('x') as stream:
        os.chmod(metadata, 0o600)
        json.dump({'rules': previous, 'display': display, 'config': config, 'engine': engine}, stream)
    try:
        run(set_command(display, config['model'] or previous['model'], ','.join(config['layouts']), config['options']))
        after = run(['xkbcomp', '-xkb', display, '-'])
        if 'hebrew_' not in after or 'English (US)' not in after:
            raise RuntimeError('The requested bilingual map did not reach Xwayland')
        current = run(['ibus', 'engine'])
        if current not in engine_groups:
            raise RuntimeError('Input source changed outside the supported pair during repair')
        lock_group(display, engine_groups[current])
    except Exception:
        run(set_command(display, previous.get('model', 'pc105'), previous['layout'],
                        previous.get('options', '').split(',') if previous.get('options') else [],
                        previous.get('rules'), previous.get('variant')))
        run(['xkbcomp', str(backup), display])
        raise
    return {'status': 'REPAIRED', 'display': display, 'layouts': config['layouts'],
            'active_source': current, 'scope': 'current shared Xwayland display',
            'persistent_gnome_settings_changed': False, 'background_service': False}
