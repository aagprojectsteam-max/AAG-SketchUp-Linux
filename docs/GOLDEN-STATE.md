# Final Golden configuration

Technical validation: **2026-09-28**, Asia/Jerusalem. Release identity: annotated tag **stable-sketchup-2026-ubuntu-final**. The release commit is resolved from that tag (`git rev-parse stable-sketchup-2026-ubuntu-final^{commit}`), avoiding an impossible self-referential commit hash inside its own tree. The final user report and private publication receipt record the verified hexadecimal commit.

| Item | Validated value |
| --- | --- |
| SketchUp | 26.1.252 x86-64, original unpatched executable |
| Host | Ubuntu 26.04.1 / kernel 7.0.0-34-generic |
| Desktop | GNOME 50.1 / Wayland with Xwayland / existing scale 2x |
| GPU | Intel Arc MTL / Core Ultra 7 155H |
| Driver/API | Mesa 26.0.8-1ubuntu0.3 / OpenGL 4.6; Vulkan capability 1.4.341 |
| Wine/Proton | GE-Proton10-25 / Wine 10.0 Staging / documented Wine touch-export alias |
| Container | sniper 3.0.20260805.254768 / pressure-vessel 0.20260805.0 |
| App | `$SKETCHUP_ROOT/app/SketchUp.exe` |
| Prefix | `$SKETCHUP_ROOT/compatdata/pfx` |
| Launcher | `$SKETCHUP_ROOT/bin/launch-sketchup.py` |
| DPI | 192 plus prefix-local HIGHDPIAWARE |
| Graphics | Classic hardware OpenGL / 8x MSAA / fast feedback off |
| Native viewport | 2166x1616 pixels at tested maximized layout |
| Steam client | Not required; uninstalled |
| Final rollback | `$PROJECT_ROOT/backups/final-golden-20260928/installation` |
| Protected earlier rollback | `$PROJECT_ROOT/backups/pre-finalization-20260928-080531` |

The machine's exact private paths are retained in its local finalization records; public commands use placeholders. The installed launcher resolves its canonical root automatically.

## Required components

User-owned complete app/content; corrected x64 MSVCP140; native x64 UCRT and override; StyleTemplate.skp and bundled ProgramData; exact private GE-Proton/sniper; the guarded Wine touch fix; host Intel/Mesa; Python/systemd/Xwayland and desktop utilities. Hashes and reproduction commands are in [INSTALL.md](INSTALL.md) and [ROOT-CAUSE.md](ROOT-CAUSE.md).

## Historical and failed experiments

Steam client/login, runtime4, GE-Proton11-7, UMU, alternate system Wine versions, software rendering, Zink, virtual desktop, CEF debug ports, Qt environment scaling trials and input LD_PRELOAD filters are not required. The failed migration of a prefix from a temporary path is documented; create/restore directly at the final path.

## Acceptance and limits

The complete [matrix](acceptance.json) and [test explanation](TEST-MATRIX.md) record final physical-input, model/save/reopen, desktop, cleanup, rendering and cold-start validation. Every mandatory technical gate passed before repository creation. Publication is finalized only after commit/tag push and remote verification. The working tree must then be clean.

No new BugSplat occurred in final regression. Each of the three final cold launches closed without remaining canonical-prefix processes. The original Input Lock and pointer settings are restored. The final backup matched the closed installation and original installer hashes remained intact. The real Windows installation and unrelated Wine applications were untouched.

Limits: basic local modeling on the recorded machine; no reboot/logout test, automatic SKP association, full touch gestures, honored fullscreen request, cloud/licensing validation for other users, or large production workload guarantee. Private Steam remnants and protected rollback archives remain within the user's approved retention scope.

## Release

FINAL_GOLDEN=YES for the published, verified annotated release tag.

Repository: [AAG-SketchUp-Linux](https://github.com/aagprojectsteam-max/AAG-SketchUp-Linux).

Tag: [`stable-sketchup-2026-ubuntu-final`](https://github.com/aagprojectsteam-max/AAG-SketchUp-Linux/releases/tag/stable-sketchup-2026-ubuntu-final).

Verify the exact commit with `git rev-parse stable-sketchup-2026-ubuntu-final^{commit}` and compare it with `git ls-remote origin refs/heads/main refs/tags/stable-sketchup-2026-ubuntu-final refs/tags/stable-sketchup-2026-ubuntu-final^{} `. The final local report includes the hexadecimal commit and remote receipt.
