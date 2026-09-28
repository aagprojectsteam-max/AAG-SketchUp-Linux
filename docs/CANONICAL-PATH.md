# Canonical architecture

`$SKETCHUP_ROOT` is the single persistent production installation. The launcher's location resolves it automatically; `--root` is available for explicit diagnostics.

```text
$SKETCHUP_ROOT/
  app/                         User-supplied SketchUp 26.1.252
  compatdata/pfx/               Private Windows prefix
  runtime/GE-Proton10-25/       Required compatibility runtime
  runtime/SteamLinuxRuntime_sniper/  Required Linux container runtime
  runtime/client/              Empty compatibility client path
  config/fontconfig.conf       SketchUp-scoped font configuration
  bin/launch-sketchup.py       Canonical entry point
  bin/install-launcher.py      GNOME integration
  bin/collect-diagnostics.py   Local support metadata
  logs/                        Private launch diagnostics
  backups/                     Desktop integration rollback records
```

The Apps entry and optional desktop shortcut call the same installed launcher. The Dock pins the Apps entry. Persistent absolute paths are written into that user's desktop file; no temporary directory or source checkout is required at runtime.

Launch chain:

```text
GNOME Apps / Dock
  -> installed Python launcher
  -> user systemd service aag-sketchup-2026.service
  -> sniper _v2-entry-point --verb=run
  -> GE-Proton10-25/proton run
  -> app/SketchUp.exe
```

The service uses `Restart=no`, `RuntimeMaxSec=infinity`, `ExitType=cgroup` and `KillMode=control-group`. A lock prevents launch races; detection is scoped to this installation's compatibility-data path. The service belongs to the user and needs no sudo. Wine processes for other applications are outside its scope.

The environment is defined in [launch-sketchup.py](../scripts/launch-sketchup.py). Key choices are Xwayland (`PROTON_ENABLE_WAYLAND=0`), Classic/OpenGL preferences, CEF GPU disable scoped to web UI, app ID zero and an empty Steam compatibility client directory. CEF debug-port and Qt scaling variables are unset. Wine DPI is 192 with a prefix-local HIGHDPIAWARE layer; Classic MSAA is 8x. The exact GE Wine user32.dll includes the documented missing-touch-export fallback. The global GNOME scale and global shell environment are unchanged.

## Required components

Complete user-owned app/content, x64 MSVCP140, native x64 UCRT, GE-Proton10-25, complete sniper, host Intel/Mesa graphics, Python, systemd user session, Xwayland and desktop integration tools.

## Historical experiments

Steam client/login, Steam game shortcut, GE-Proton11-7, runtime4, system Wine 11, UMU, Zink/llvmpipe, a Wine virtual desktop, CEF remote-debug ports and old accumulated dependency experiments are not components of the fresh-prefix setup recipe. Proton's own default prefix settings remain part of its runtime.
