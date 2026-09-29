# Troubleshooting

Set `SKETCHUP_ROOT` to your persistent installation root. Close and save SketchUp normally before changing its files. Back up the prefix, preferences and replaced files first. Other Wine applications are independent; never use a global `killall wine` or `wineserver -k`.

## Start with a local diagnostic report

```bash
"$SKETCHUP_ROOT/bin/launch-sketchup.py" --check
"$SKETCHUP_ROOT/bin/collect-diagnostics.py"
"$SKETCHUP_ROOT/bin/launch-sketchup.py" --debug
```

The collector emits file hashes, architecture, DPI, selected renderer preferences and service status. It excludes models, browser/account data and raw dumps. Detailed per-launch logs are under `$SKETCHUP_ROOT/logs/`; the exact command and scoped environment are in `manifest.json`. Application logs are usually under `compatdata/pfx/drive_c/users/steamuser/AppData/Local/Temp/SketchUpLog-*.log`. Review any logs manually before sharing: model paths and account information can appear there.

## SketchUp does not start

Check the launcher's error notification and `--check`. Confirm complete runtime directories and a user graphical session with `DISPLAY`, Xwayland authorization and a working systemd user manager. A pressure-vessel error occurs before SketchUp and should be fixed as a container/host problem. Replacing DLLs will not repair a missing runtime payload.

```bash
systemctl --user status aag-sketchup-2026.service
journalctl --user -u aag-sketchup-2026.service -n 60 --no-pager
```

If SketchUp is still starting, the launcher will refuse a duplicate instance. Wait for startup or inspect the logs. If it is genuinely hung, save any recoverable work and stop **only** this service with `systemctl --user stop aag-sketchup-2026.service`; unsaved changes in this application may be lost. Inspect the failure before another launch.

## ARM64/x64 mismatch or missing runtime DLL

`c000007b` on MSVCP140 together with dependent `c0000135` errors was caused by an ARM64 file in this x64 setup. Check both `app/msvcp140.dll` and prefix `windows/system32/msvcp140.dll`. `file` should identify PE32+ x86-64. The launcher checks the PE machine field itself. Use the legitimate file and hashes in [INSTALL.md](INSTALL.md); do not fetch an arbitrary DLL from a download site.

A fresh prefix can also exit with `unexpected ucrtbase.dll`, emitted by embedded Ruby. Install the verified native x64 UCRT and its `native,builtin` override from the installation guide. A secondary Xalia teardown error does not establish Xalia as the root cause.

## Welcome works, modeler crashes / missing content

Verify:

```text
compatdata/pfx/drive_c/ProgramData/SketchUp/SketchUp 2026/SketchUp/Styles/StyleTemplate.skp
```

An empty Styles directory caused the confirmed `SketchUp.exe+0x777a50` null access. Restore the correct content from your own installation material, with a backup. Copying only the application executable/tree can omit required ProgramData content. The repair and file hash are in [ROOT-CAUSE.md](ROOT-CAUSE.md).

## BugSplat

Record the launch time, action, runtime version and latest application/Wine log. Preserve a private dump only when needed for local diagnosis. Raw dumps may include memory contents and personal data; do not attach them to the public repository. Distinguish the historical Qt window-creation crash from the later missing-style-model crash. A generic BugSplat dialog does not identify a root cause.

## Bad pixel format / OpenGL context / DX12

Confirm hardware rendering with `glxinfo -B` and the application's own `GL_RENDERER` and graphics API log lines. The tested path is Intel Arc, Mesa 26.0.8, Classic/OpenGL 4.6, 8x MSAA and fast feedback off. Avoid interpreting a loaded Vulkan software-driver library as proof that the OpenGL viewport uses software rendering; use the actual renderer string.

DX12 successfully created a device in one historical test but then crashed on the missing style resource. It is not the final validated path. Restore the documented Classic settings before comparing a new failure. Keep GPU/driver changes separate from application content repairs. Do not add llvmpipe, Zink or a virtual desktop as an unexplained permanent workaround.

## Tiny UI / pointer offset / clipping

The installation uses prefix-only `HKCU\Control Panel\Desktop\LogPixels=192` and the default `HIGHDPIAWARE` value under `HKCU\Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers`. Both are necessary for the tested Qt/CEF combination. Close SketchUp before editing the prefix registry and back it up. A complete restart of that prefix is required. The production launcher unsets Qt scale-factor variables to avoid stacking Qt scaling on native Wine DPI. GNOME global scaling is unchanged.

If a different display needs another size, try a fresh backup and a moderate value such as 144, then repeat real menu, toolbar, tray and dialog hit tests. A screenshot cannot prove correct pointer coordinates. Restore the previous value if clicks are offset or controls clipped. Test maximization and restored geometry as well.

## Duplicate Dock icon or launcher opens another copy

Use the installed `aag-sketchup-2026.desktop` entry. Its `StartupWMClass=steam_app_0` matches the launcher using Steam app ID zero. The title should be **SketchUp 2026**; the icon comes from the user's local app tree. Remove an obsolete pinned launcher through the Dock UI and pin the canonical Apps entry. Do not change unrelated favorites.

The launcher's existing-instance path raises windows on the current workspace. A file argument while SketchUp is already open asks the user to use File > Open. Automatic SKP file association is intentionally outside the required scope.

## Steam unexpectedly opens

Steam is not a client dependency of this architecture. Search for old Steam URI launchers, delayed shell jobs, user services/timers, autostart entries and YAWMS saved sessions. Remove only records belonging to the old SketchUp experiment. Keep YAWMS's unrelated saved sessions and settings. Flatpak masks and background blocks should not remain as substitutes for removing stale launch triggers.

## Stale Wine/Proton/webhelper processes

The application runs in one user systemd cgroup. After normal closure, verify the service is inactive/collected and inspect processes using this exact `STEAM_COMPAT_DATA_PATH`. Do not classify unrelated Wine sessions as leftovers. If this prefix remains active, capture its logs and process information before stopping its service. The wrapper does not restart a crashing application or hide the crash with a retry loop.

## Saved model will not reopen

Preserve the original and `.skb` backup. Test File > Open on a copy and inspect the application log. A launcher model argument must refer to an existing local file; paths with spaces are supported. Confirm it is a compatible SketchUp model and that the same app/runtime/content versions are still installed. Do not overwrite the original while testing. Compare geometry visually after reopening, not just the window title.

## Updates

A new SketchUp, Proton, sniper, Mesa or major desktop version invalidates assumptions in the recorded acceptance matrix. Make a rollback copy, change one component at a time and rerun the model/save/reopen/desktop/DPI checks. Keep the documented working runtime until the new one passes.

## Touch crashes / missing Wine export

`unimplemented function USER32.dll.GetPointerFrameTouchInfo` identifies a separate Wine compatibility issue. The setup applies `patch-wine-touch.py` to the exact supported Wine DLL and keeps its original. The launcher rejects a missing or changed fix before starting. Do not apply it to Microsoft user32.dll or a different Wine build. The fallback ignores unsupported direct-touch frames safely; use a mouse or touchpad for modeling. It is not full multitouch support. Re-run normal GUI regression after any runtime update.

## Jagged edges or a soft viewport

Use Classic graphics with AAMethod=8 and fast feedback off, then fully restart SketchUp. Inspect the physical viewport dimensions, not only a scaled screenshot. The tested 192-DPI layout renders at 2166x1616 native pixels. Do not compensate with lower desktop resolution, software rendering or a blur filter. See [the controlled AA comparison](GRAPHICS.md).

## Window behavior and input testing

Maximize and restore passed. A window-manager fullscreen request was ignored in the tested setup; use maximize. During automated testing on Wayland, X11 mouse warps and uinput clicks can refer to different pointer positions. This is a harness error, not proof of application pointer offset. All final click tests used consistent logical desktop coordinates and verified the selected geometry. Respect the user's Input Lock state and restore any temporary unlock or pointer configuration after tests.

## Black dialogs and first-frame popup flash

Post-Golden regression found two distinct paths: retained HTML client contents
after focus changes, and an X11 window mapped with an uninitialized black
background before its first raster paint. Candidate A/B tests support a
prefix-local `ClientSideGraphics=N` setting plus an original, guarded raster
presentation helper. See [the evidence and rejected experiments](WINDOW-PAINTING.md).
Do not reduce DPI/MSAA, enable a software modeler or globally change the compositor.
The exact upstream change causing the retained HTML defect remains unproven.

### Instrumented close and baseline runtime warning

A temporary QA-timer candidate once crashed on immediate close. Root cause is unresolved; three candidate and three production launches after removing QA passed. The bundled Xalia ReleaseChildren warning also exists in Base logs; it is not a plugin-load failure. See [bounded evidence](WINDOW-PAINTING.md#instrumented-rapid-close-crash-and-retest).

## Future update preparation errors

Use [UPDATE.md](UPDATE.md) for missing/ambiguous PE builds, wrong architecture, incomplete content/runtime, existing candidates and rollback failures. A rejected candidate is not a reason to overwrite production. Prefix initialization needs the normal HOME environment and the recorded GE non-Steam flags; the framework self-test caught and fixed both omissions. A partial failed prefix is retained for review and must not be blindly merged.

## Secure Internet connectivity

A host CA path can exist in Ubuntu but be absent inside sniper. The networking
helper supplies a validated private copy. Embedded Ruby needs the separate
prefix-local bootstrap because SketchUp resets its SSL certificate environment.
Use [NETWORKING.md](NETWORKING.md) for the comparisons and negative TLS tests.

Service-specific outcomes remain separate: Connect can require its own terms;
Generate Report can show a host filtering-policy block; Add Location address
search can work while its map fails WebGL initialization. Do not remove the
validated CEF GPU setting or bypass network policy merely to hide these limits.

## GNOME shows Hebrew but SketchUp still types English

Compare `ibus engine`, GNOME input sources and the actual map from `xkbcomp -xkb "$DISPLAY" -`. In the reproduced failure GNOME selected Hebrew while Xwayland contained US symbols only; native Wayland worked and plain X11 also failed. The canonical launcher now repairs this exact mismatch once per cold start. Verify real Unicode input and live switching; the indicator and Wine HKL alone are insufficient.

See [HEBREW-INPUT.md](HEBREW-INPUT.md) for diagnostic commands, supported-map guards, private map backups and rollback. Preserve account state and avoid blind keyboard registry edits. Mixed RTL alignment is a separate application display limitation.
