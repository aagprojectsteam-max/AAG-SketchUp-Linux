# Final engineering report

## Executive summary

The canonical Linux installation passed the final technical acceptance for SketchUp **26.1.252 x64** on Ubuntu 26.04.1. It uses a private GE-Proton10-25/sniper runtime, native Intel OpenGL, 192 DPI and 8x MSAA. Real modeling, navigation, save/reopen, Apps/Dock, focus, window restore/maximize and three cold launches passed. No new BugSplat appeared in final validation and each normal close left zero prefix processes. This is bounded validation of the documented configuration, not a guarantee of indefinite or workload-independent stability.

## Working architecture

`$SKETCHUP_ROOT/app` contains the unmodified supplied executable. `compatdata/pfx` is the private Windows environment. `runtime/GE-Proton10-25` and `runtime/SteamLinuxRuntime_sniper` are required. `bin/launch-sketchup.py` resolves its installed root and launches one user systemd cgroup. Apps and Dock share one desktop entry. No Steam client, UMU, system Wine or temporary directory is required.

## Original symptoms and confirmed repairs

1. ARM64 MSVCP140 in an x64 process caused c000007b/c0000135 loader errors and exit 53. The legitimate supplied x64 14.51.36247.0 library replaced both affected copies. Its original introduction is unknown.
2. Missing `Styles/StyleTemplate.skp` caused a repeatable null access at SketchUp.exe+0x777a50 after graphics initialization. Restoring that file from existing local content removed the crash; 481 missing bundled resources were then restored. Why the earlier assembly omitted content is unproven.
3. Fresh-prefix embedded Ruby rejected builtin UCRT. The verified native x64 10.0.10586.15 UCRT and native,builtin override fixed it.
4. Wine's missing GetPointerFrameTouchInfo export aborted on real touch input. A hash-guarded metadata-only export alias now returns unsupported input safely. No proprietary executable was patched.
5. Wine DPI alone left CEF and Qt disagreeing about geometry. The prefix's HIGHDPIAWARE registry layer fixed Welcome painting and hit targets at 192 DPI.

Exact hashes, paths, fault offsets, evidence boundaries and failed alternatives are in [ROOT-CAUSE.md](ROOT-CAUSE.md).

## Graphics, DPI and performance

Classic OpenGL/WGL uses Intel Arc MTL through host Mesa 26.0.8. Live renderer strings and renderD128 descriptors confirm hardware rendering. DXVK/Vulkan probing does not make the Classic modeler a D3D renderer. CEF alone uses its disabled-GPU path.

Controlled AA 0/2/4/8 comparisons used identical geometry, camera, 3072x1856 window and display scaling. The 2166x1616 native framebuffer corresponds to 1083x808 logical viewport coordinates. 8x improved diagonal edge and axis coverage without a post-process blur. Mean simple-scene redraw was 18.77 ms versus 18.52 ms at 4x. Idle CPU was about 3% of one core; summed process RSS 2.10 GiB includes shared mappings. See [GRAPHICS.md](GRAPHICS.md).

Wine 192 DPI enlarges native menu, toolbar, status, tray and dialog controls. Real face/edge IDs and line endpoints verified correct mouse coordinates. Restored windows changed the framebuffer to match their actual size. Fullscreen was not honored by the tested window-manager request; maximize and restore passed.

## GNOME Apps and Dock

The canonical `aag-sketchup-2026.desktop` has the original 512-pixel icon extracted locally from the user's executable, `Terminal=false`, and `StartupWMClass=steam_app_0`. Actual Apps/Dock clicks launched the app. Dock focus raised a minimized window. Calling the launcher when the app was on another workspace moved/raised it without creating another process. No duplicate SketchUp Dock icon was observed.

## Steam, session management and cleanup

Steam client dependency is **NO**. The client was uninstalled and all 17 explicitly approved obsolete paths were deleted after dependency checks. Their pre-delete allocated sizes total 56.41 GiB. GE-Proton/sniper remain at the canonical path. Private account data outside the approved deletion lists are retained and unused.

YAWMS is enabled with its intended unrelated settings. Stale Steam sessions and three old window mappings were archived/removed. No obsolete masks, Steam URI jobs or CEF debug listeners remain. The original Input Lock state and pointer settings were restored. Historical workspace prefixes are consolidated as private recovery material, with no production launcher references. [CLEANUP.md](CLEANUP.md) records each deletion and retained component.

## Final regression

Real Line, Rectangle, Push/Pull, Selection, Delete, Orbit, Pan, Zoom, tray, menu and dialog input passed. A new SKP file was saved through the GUI and reopened after normal close; all 12 edge endpoint pairs and six faces matched. Temporary Ruby observers and failed input shims were archived before the final three cold launches. Those launches passed, including two saved-model opens and one new template, with no new dumps or final-log crash signatures. Other Wine applications were left running independently. Full results and measured observation periods are in [TEST-MATRIX.md](TEST-MATRIX.md).

## Reproduction and rollback

[INSTALL.md](INSTALL.md) specifies exact runtime versions, legitimate source inputs, native UCRT extraction, architecture/hash checks, DPI, AA, the Wine fix and desktop setup. Four original support-code regression tests passed. The final backup `backups/final-golden-20260928/installation` was compared with the closed installation, including symlink targets, with no difference. The explicitly protected pre-finalization rollback also remains. Restore to the same canonical path; see [UNINSTALL-ROLLBACK.md](UNINSTALL-ROLLBACK.md).

## Publication and release identity

The dedicated public repository is [AAG-SketchUp-Linux](https://github.com/aagprojectsteam-max/AAG-SketchUp-Linux). Only original code, documentation, hashes and sanitized native edge crops are in the public allowlist. No proprietary DLL/executable/installer, prefix, model, account data or raw crash dump is published. The exact release commit is the commit referenced by annotated tag `stable-sketchup-2026-ubuntu-final`; use `git rev-parse stable-sketchup-2026-ubuntu-final^{commit}`. Remote commit/tag verification and a clean worktree are required by the release workflow before the user receives FINAL_GOLDEN=YES.

## Limits

No reboot/logout was coordinated. Persistent paths and three cold launches were verified within the existing login. SKP file associations were intentionally left unchanged. Cloud services, another account's licensing flow, LayOut, printing, third-party extensions, multitouch gestures and large/long-duration workloads remain outside this validation. These limits do not conceal a failed mandatory basic-modeling gate.
