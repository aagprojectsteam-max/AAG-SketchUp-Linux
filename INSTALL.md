# Install SketchUp on Ubuntu

Use the complete [installation guide](docs/INSTALL.md) for verified file hashes, UCRT extraction, runtime downloads and all settings. The tested combination is SketchUp 26.1.252 x64, GE-Proton10-25, sniper 3.0.20260805.254768 and Intel/Mesa on Ubuntu 26.04.1.

## Required inputs

You must provide your own legitimate SketchUp application tree, bundled ProgramData content, x64 MSVCP140 and native x64 UCRT. The repository contains none of those binaries. Supply complete extracted GE-Proton and sniper directories too. Setup never accepts legal terms or activates a license.

Install host utilities:

```bash
sudo apt install python3 coreutils systemd bubblewrap wmctrl desktop-file-utils \
  xdg-user-dirs libglib2.0-bin libnotify-bin fontconfig fonts-liberation icoutils
```

## Create a new permanent installation

Adjust source paths to your own files. The destination must not already exist.

```bash
SKETCHUP_ROOT="$HOME/Applications/SketchUp2026"
SKETCHUP_SOURCES="$HOME/SketchUp-sources"
python3 scripts/prepare-installation.py \
  --root "$SKETCHUP_ROOT" \
  --app-source "$SKETCHUP_SOURCES/application-26.1" \
  --content-source "$SKETCHUP_SOURCES/programdata-content" \
  --msvcp-x64 "$SKETCHUP_SOURCES/application-26.1/msvcp140.dll" \
  --ucrt-x64 "$SKETCHUP_SOURCES/ucrt-x64/ucrtbase.dll" \
  --proton-source "$SKETCHUP_SOURCES/GE-Proton10-25" \
  --container-source "$SKETCHUP_SOURCES/SteamLinuxRuntime_sniper" \
  --dpi 192
"$SKETCHUP_ROOT/bin/launch-sketchup.py" --check
"$SKETCHUP_ROOT/bin/launch-sketchup.py"
```

The procedure applies the documented Wine touch fallback, required DLL/content corrections, native UCRT override, 192 DPI/HIGHDPIAWARE and Classic 8x MSAA. Use the exact supported inputs; a different Wine DLL hash is refused.

After you personally handle any terms/licensing prompts and verify modeling:

```bash
python3 "$SKETCHUP_ROOT/bin/install-launcher.py" --root "$SKETCHUP_ROOT"
```

Open **SketchUp 2026** in GNOME Apps and pin that entry to the Dock. Test a new model, selection/drawing, orbit/pan/zoom, save/reopen and normal close. No Steam client or sudo is needed for everyday launching. Keep a [rollback copy](docs/UNINSTALL-ROLLBACK.md) and review [known limitations](README.md#limits).

## Popup painting support

The current support build also needs a C compiler, binutils and X11/XCB/XRender
development headers (`build-essential binutils libx11-dev libxcb1-dev libxrender-dev`
on Ubuntu). Preparation builds the original local popup helper; no vendor
DLL is modified for this fix. See [window painting](docs/WINDOW-PAINTING.md) for scope, tests and rollback.
