# Hebrew input on GNOME Wayland

## Confirmed cause

GNOME had US and Hebrew input sources. IBus changed between the two engines,
while the current desktop Xwayland server had only `pc+us+inet(evdev)` in its
actual keyboard map. It contained no Hebrew key symbols. The same mismatch
was present on the core, XTEST and Xwayland keyboard devices.

This explains the observed failure before Wine: the GNOME indicator changed
to Hebrew, but X11 applications received English. The origin of that map
mismatch is **not established**. We have not attributed it to IBus, GNOME,
Input Lock or another application without evidence.

The confirmed path is:

| Surface | Original map | Corrected map |
| --- | --- | --- |
| GTK3 using native Wayland | English/Hebrew/live switching passed | Preserved |
| GTK3 using X11/Xwayland | Hebrew selection produced Latin | English/Hebrew/live switching passed |
| Win32 EDIT in the canonical Proton environment | Hebrew selection produced Latin | English/Hebrew/live switching passed |
| SketchUp Qt and CEF | User reported English in Hebrew mode | Actual Unicode Hebrew and live switching passed |

The controlled comparison kept the **same Wine process** running. Adding the
existing GNOME `us,il` pair fixed its four edit controls. Restoring the original
map reproduced the failure. Reapplying the bilingual map fixed it again.
No Wine registry or input-method environment change was required.

Wine's `GetKeyboardLayout` and layout list still reported `0409` after the
repair. That diagnostic does not override the actual Unicode received by the
edit controls. We did not insert guessed keyboard-layout registry values.

## Final fix and scope

[The keyboard helper](../scripts/keyboard-environment.py) runs once from the
canonical launcher, before a cold start. Apps and Dock use that launcher.

It changes the **current shared Xwayland display map**. Its invocation belongs
to SketchUp, but its effect is not isolated to a Wine prefix. This was necessary
because the failure was also reproduced in a plain X11 application. Other X11
applications on that display receive the corrected existing bilingual layout.
The unrelated nested X server was not changed.

The helper:

1. Requires GNOME on Wayland and the XWAYLAND extension on the caller's local
   `DISPLAY`.
2. Supports the existing US/Hebrew source pair, in either order. Other source
   combinations are left unchanged.
3. Leaves an already bilingual map unchanged.
4. Repairs only the demonstrated US-only map. It refuses an unfamiliar map
   that needs review, rather than overwriting a custom layout.
5. Backs up the exact XKB map and its rules properties into the private launch
   directory before changing it.
6. Builds the map from the user's existing GNOME model, layouts and XKB options.
   If GNOME leaves its model unset, it retains the current XKB model.
7. Verifies that English and Hebrew reached Xwayland, then selects the group
   matching the current IBus engine. This preserves an initially selected Hebrew
   source as well as English.
8. Restores the previous rules and exact map if repair or verification fails.

There is no polling service, key logger, character remapper, clipboard typing,
registry alteration or persistent GNOME input-source change. Normal source
switching works while SketchUp stays open. `--check` performs no input mutation.

Dependencies are `gsettings`, `ibus`, `setxkbmap`, `xkbcomp`, `xdpyinfo` and libX11
on the host. On Ubuntu, the X11 tools are supplied by `x11-xkb-utils` and
`x11-utils`; GNOME already supplies the input-source infrastructure.

## Actual input tests

Tests pressed physical evdev keys in owned test controls. They did not inject
Unicode strings or paste Hebrew from the clipboard. The same keys produced
`cshe, gcrh, 123!` in English and `בדיקת עברית 123!` in Hebrew. English → Hebrew
→ English → Hebrew was tested without restarting each application.

| Surface | Toolkit evidence | Verification |
| --- | --- | --- |
| Standalone Linux fields | GTK3 Wayland / GTK3 X11 | Exact strings and codepoints |
| Standalone Windows fields | Standard Win32 EDIT | Exact UTF-16 codepoints and HKL |
| Ruby Console | `Qt691QWindowIcon` | Evaluated typed string literals, exact Unicode |
| SketchUp `UI.inputbox` | `Qt691QWindowIcon` | Ruby-returned values and codepoints |
| Owned HtmlDialog | CEF HTML | DOM values/codepoints through an action callback |
| Text annotation tool | SketchUp model text | Typed mixed text, `Sketchup::Text#text` and codepoints |
| Save As | SketchUp file dialog | Physically typed Hebrew folder and filename; new file created |
| SketchUcation 5.0.6 | Plugin CEF UI | Visible English/Hebrew in an empty username field, then cleared; never submitted |

The plugin check was visual; a DOM callback was not obtained on that plugin.
It is not presented as an instrumented plugin codepoint capture. Exact Unicode
was independently verified in the owned CEF dialog and SketchUp model text.
No password was entered, no account was used and no activation was performed.

Entity Info's existing auto-hidden tray did not expand during this test, so
no Entity Info field result is claimed. Model-text persistence was verified
with an actual text annotation instead. Measurements accepts numeric/tool
values and was exercised with an explicit unit during Push/Pull, not treated
as a free-text Hebrew field.

## Filenames, storage and RTL

A new owned test model was saved using a Hebrew directory and filename. It was
opened from the recent-files screen after a complete cold launch. Its Hebrew
annotation, exact codepoints, faces, edges and groups matched the saved model.
No pre-existing user SKP was overwritten.

Use Windows-style backslashes when entering an absolute path in this build's
Save As filename field. A forward-slash path was rejected by that dialog's
filename validation; retrying the same Hebrew components with backslashes
succeeded. This was a path-entry error, not a Unicode failure.

Input correctness is PASS. RTL display is PARTIAL: Hebrew glyphs are readable,
but mixed Latin/Hebrew/digits/punctuation follow each control's bidirectional
layout and alignment. No font substitution or global RTL setting was applied.

## Regression and evidence

Three cold runs were observed for about 309 seconds (Apps), 562 seconds
(Dock) and 602 seconds (canonical launcher). Apps repaired the reproduced
US-only map with English selected; the third launch repaired it with Hebrew
already selected, and its first typed phrase had the expected Hebrew codepoints.
The Dock run used an already-correct map. All three closed with zero remaining
prefix processes. Later unsaved test edits were explicitly authorized for
discard by the user; the earlier saved test file was retained.

The sanitized [acceptance matrix](hebrew-input-acceptance.json) distinguishes
current verification from historical Base/Plugin Golden evidence. Private
screenshots, test models, keyboard maps, input-control values, session details
and raw logs remain outside Git.

Modeling was exercised through the actual GUI: line, rectangle, Push/Pull,
selection, orbit, pan and zoom. Geometry and camera changes were checked through
the Ruby API. For an orthographic camera, zoom was verified using camera height;
unchanged eye/target alone does not indicate a failed zoom.

A GUI attempt without a sufficiently specific focus guard reached a Create
Component dialog in the owned model. It was cancelled. The plugin input test
was repeated with the exact target window asserted before every key. No user
model or external account was affected. The first line-tool attempt was also
repeated after leaving the previous text-edit context; an actual new edge was
then verified. These incomplete attempts are not counted as passes.

The historical [networking diagnostic X11 error](NETWORKING.md) remains in the
technical history. This input repair does not claim to explain that earlier
instrumented experiment.

## Auxiliary runtime exception

The third input cold run logged one `Unhandled exception in Xalia` with
`ReleaseChildren should not create new children`, plus handled invalid-window
messages. Xalia is Proton's auxiliary UI integration process. SketchUp stayed
running, its input probe returned the expected Unicode, and there was no
SketchUp fatal X error or new BugSplat dump. The first two input cold logs had
no unhandled exception entry. This is retained as an auxiliary-runtime
limitation; the complete third log is not claimed to be error-free. No Xalia
configuration was changed as part of the input repair.

## Diagnosis

Run these in the same GNOME session/display that starts SketchUp:

```sh
printf '%s\n' "$XDG_SESSION_TYPE" "$DISPLAY" "$WAYLAND_DISPLAY"
gsettings get org.gnome.desktop.input-sources sources
gsettings get org.gnome.desktop.input-sources xkb-model
gsettings get org.gnome.desktop.input-sources xkb-options
ibus engine
setxkbmap -query
xkbcomp -xkb "$DISPLAY" - | rg 'xkb_symbols|name\[group|hebrew_'
```

For the tested pair, expect US and Hebrew in GNOME and both layouts in the
actual XKB map. `ibus engine` should agree with the selected source.
`gsettings ... current` may be stale and is not adequate evidence by itself.
The Wine HKL alone is also insufficient: verify actual input.

The launch manifest contains a `keyboard` result: `REPAIRED`, `ALREADY_PRESENT`
or `NOT_APPLICABLE`. Unsupported maps fail with a review message. That message
is not a license/login request and should not be worked around by resetting
an authenticated prefix.

## Rollback

Close SketchUp normally after saving work. Restore the previously backed-up
launcher to the same installation's `bin/launch-sketchup.py`; leave the newer
helper file unused. This does not reset networking, accounts, plugins or Wine
registries. Keep the backup until a replacement is validated.

For a deliberate session-map rollback, review `xwayland-before.json` from the
specific launch that performed the repair. Restore those `setxkbmap` rules,
model, layout, variant and options to that same display, then apply its exact
`xwayland-before.xkb` with `xkbcomp`. Do not target a different X display or
replace GNOME's saved source list. Restoring the original faulty map will
reproduce the Hebrew problem until repaired again.

## Future updates

The update framework now blocks promotion without English input, Hebrew input,
live switching, English shortcuts, Hebrew filenames, Hebrew save/reopen,
CEF Hebrew, plugin-input review and Hebrew after a cold start. Apps and Dock
also have separate post-promotion Hebrew gates. Pointer accuracy remains a
mandatory existing gate.

The repair is conditional. A future GNOME/Wine/runtime combination that
propagates the complete map already should return `ALREADY_PRESENT`. Validate
the full bilingual regression before removing the helper or expanding its
supported layout combinations.

## Reproduce with original test sources

Use only harmless test phrases; generated JSON contains the test field values
and stays private. The probes have no global keyboard hooks.

- [GTK probe](../tests/input-gtk.py): run once with `GDK_BACKEND=wayland` and
  once with `GDK_BACKEND=x11`, passing a label and a new private JSON path.
  Type in all four fields using normal desktop language switches.
- [Win32 EDIT probe](../tests/input-win32.c): compile locally with
  `x86_64-w64-mingw32-gcc -municode tests/input-win32.c -o /tmp/input-win32.exe -luser32`.
  Run it with one argument: a new private Windows output-file path, through
  the same canonical runtime. Its report includes only its own fields and
  keyboard-layout APIs. Compiled binaries are not distributed.
- [SketchUp probe](../tests/input-sketchup.rb): load this source in Ruby Console,
  then call `AAGBilingualProbe.run` with a new private directory in Windows
  path syntax. Test its Qt dialog and CEF fields. It does not read or modify
  the open model.

For the standalone Windows probe, close SketchUp normally first. This Python
example uses the installed launcher's environment and container entry helpers:

```python
import os, runpy, subprocess, tempfile
from pathlib import Path
root = Path(os.environ['SKETCHUP_ROOT']).resolve()
api = runpy.run_path(str(root / 'bin/launch-sketchup.py'))
get_processes = api['processes']
make_environment = api['environment']
assert not get_processes(root / 'compatdata'), 'Close SketchUp normally first'
private = Path(tempfile.mkdtemp(prefix='sketchup-input-probe-'))
env = os.environ.copy()
env.update(make_environment(root, private))
for key in ('WAYLAND_DISPLAY', 'WINEPREFIX', 'LD_PRELOAD', 'LD_LIBRARY_PATH',
            'SU_CEF_DBG_PORT', 'QT_SCALE_FACTOR'):
    env.pop(key, None)
subprocess.run([
    str(root / 'runtime/SteamLinuxRuntime_sniper/_v2-entry-point'),
    '--verb=run', '--', '/usr/bin/python3', str(root / 'bin/runtime-exec.py'),
    str(root), str(root / 'runtime/GE-Proton10-25/proton'), 'run',
    'Z:/tmp/input-win32.exe', 'Z:' + str(private / 'fields.json')
], env=env, check=True)
assert not get_processes(root / 'compatdata'), 'Review remaining test processes'
```

Close the probe normally to finish. Keep its private report outside the public
repository. A complete regression also needs the actual modeling, file dialog,
Hebrew model-text save/reopen, Apps/Dock, painting and networking checks above.
