# AAG SketchUp Linux

A reproducible Ubuntu setup for legitimate **SketchUp 2026 (26.1.252, x86-64)** files, using a private GE-Proton runtime, comfortable 192-DPI UI and hardware OpenGL with 8x antialiasing.

**Final technical acceptance passed on the tested machine.** Real modeling, save/reopen, Apps/Dock integration, mouse accuracy and three final cold launches passed without a new crash. See the [test matrix](docs/TEST-MATRIX.md), [graphics comparison](docs/GRAPHICS.md) and [release record](docs/GOLDEN-STATE.md).

**You must provide your own legitimate SketchUp installation files and license.** This repository supplies original scripts, documentation and sanitized screenshots. It contains no SketchUp/Microsoft/Windows binaries, installers, prefixes, account data or private dumps. Setup does not accept terms or activate a license.

## What makes this setup work

- Correct x64 MSVCP140 in place of the ARM64 library found in the old installation.
- Restored ProgramData content, especially the missing `Styles/StyleTemplate.skp` that crashed model creation.
- Native x64 UCRT for embedded Ruby in a fresh prefix.
- GE-Proton10-25 and sniper stored independently of Steam. **No Steam client or login required.**
- A guarded, reversible repair to one exact Wine DLL for an otherwise fatal missing touch API.
- Prefix-local 192 DPI plus HIGHDPIAWARE for Qt/CEF agreement; Classic 8x MSAA at native viewport resolution.
- A self-checking launcher, original icon extracted from your local app, single-instance focus and GNOME Apps/Dock integration.

The [root-cause report](docs/ROOT-CAUSE.md) includes hashes, evidence, failed experiments and unresolved historical hypotheses.

## Tested environment

| Component | Version |
| --- | --- |
| Hardware | HP EliteBook 840 G11, Core Ultra 7 155H, Intel Arc MTL, 64 GB |
| Host | Ubuntu 26.04.1, kernel 7.0.0-34-generic |
| Desktop | GNOME 50.1, Wayland + Xwayland, existing 2x scale |
| Modeler graphics | Mesa 26.0.8, OpenGL 4.6, Classic 8x MSAA |
| Application | SketchUp 26.1.252 x64; locally supplied 26.2 content restoration |
| Wine | GE-Proton10-25, Wine 10.0 Staging, documented touch-export fallback |
| Container | sniper 3.0.20260805.254768, pressure-vessel 0.20260805.0 |

## Install and use

Follow [INSTALL.md](INSTALL.md). Supply complete user-owned app/content directories, the two required x64 runtime files, and the exact GE-Proton/sniper directories. The setup script creates a new installation directly at its permanent location and refuses to overwrite an existing root.

Launch **SketchUp 2026** from GNOME Apps and pin that entry to the Dock. Daily use needs no terminal, sudo or Steam. The launcher retains local logs and supports `--debug`; `collect-diagnostics.py` produces a small reviewable report.

## Plugins / Extensions

The separate **Plugin Golden** adds Pipe Along Path, KBS Face Tool, SketchUcation
and LibFredo6 in their [tested scopes](docs/PLUGINS.md). JointPushPull, FredoCorner
and V-Ray are deferred by user choice. Supply your own legitimate extension files
and licenses; none are redistributed. See the [migration report](docs/PLUGIN-MIGRATION-REPORT.md),
[painting fix](docs/WINDOW-PAINTING.md) and [rollback delta](docs/PLUGIN-GOLDEN-DELTA.md).

## Future updates

Use [UPDATE.md](docs/UPDATE.md) and the [reusable Codex handoff](docs/CODEX-UPDATE-PROMPT.md).
The tooling audits a legitimate new source, creates a fresh isolated candidate,
reevaluates compatibility fixes and requires regression before explicit promotion.
The working Golden and rollback remain protected. See the [framework report](docs/UPDATE-FRAMEWORK-REPORT.md)
and [immutable release history](docs/GOLDEN-HISTORY.md). Future versions are not
assumed compatible.

## Documentation

- [Installation and exact prerequisites](docs/INSTALL.md)
- [Root causes](docs/ROOT-CAUSE.md) and [complete technical history](docs/HISTORY.md)
- [Architecture](docs/CANONICAL-PATH.md)
- [Native rendering, AA and performance](docs/GRAPHICS.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Cleanup/storage ledger](docs/CLEANUP.md)
- [Uninstall and rollback](docs/UNINSTALL-ROLLBACK.md)
- [Acceptance matrix](docs/TEST-MATRIX.md)
- [Final engineering report](docs/FINAL-REPORT.md)
- [Golden release record](docs/GOLDEN-STATE.md)

## Limits

This validates basic local modeling on one recorded configuration. Cloud sign-in/licensing for another account, untested third-party extension features, LayOut, printing and large production workloads are untested. Unsupported direct touch is safely rejected; multitouch gestures are not implemented. Maximize/restore work; the tested fullscreen request was ignored. No reboot/logout test was performed. Changes to SketchUp, Wine, Mesa or GNOME require a new regression run.

This community procedure does not imply official Trimble Linux support. The MIT license applies to the original support code/documentation, not proprietary or third-party installation material.
