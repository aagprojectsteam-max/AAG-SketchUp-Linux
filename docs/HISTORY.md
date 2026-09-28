# Investigation history

This record preserves the technical sequence while omitting account IDs, personal paths, models, binaries and raw dumps. The private evidence archive retains the original local diagnostics. Times below are local to the test machine on 2026-09-28 unless stated otherwise.

## Earlier experiments, September 23–25

Several installations/prefixes were attempted using system Wine, Wine 11, direct Proton, UMU and community `sketchup-linux` procedures. The supplied files included a 26.1 application tree and several existing 26.2 installer downloads/extractions. These were not interchangeable test results.

Classic rendering reached WGL/OpenGL context or pixel-format code; virtual desktop, software rendering, Zink and alternate antialiasing were tried without a complete stable model/edit/save result. The newer renderer could create an `ID3D12Device`, but later crashed. This excluded “device creation succeeds” as an adequate success criterion.

VC++ 2015/2019/2022, MFC, .NET 4.8/4.8.1, DirectX helpers, fonts, UIAutomation and multiple native/builtin overrides accumulated. Some installer attempts failed; preserved logs include winetricks checksum changes and an msiexec executable-path failure. None establishes the final minimum dependency set.

GE-Proton10-25 and checksum-verified GE-Proton11-7 were both tried. Steam Flatpak, a non-Steam shortcut, sniper and later runtime4 were introduced. An incomplete sniper installation was repaired through Steam validation. Welcome/CEF then worked more reliably, while modeler crashes remained. CEF remote-debug ports and small UI/debug helpers were used to inspect the transition.

Steam repeatedly reopened. Delayed debugging/Desktop Commander jobs invoked a Steam game URI; YAWMS also retained a Steam current-session entry. Temporary masks/background restrictions and disabling YAWMS limited symptoms. The finalization task requires removal of those triggers and restoration of unrelated session management.

## Fresh evidence and fault isolation

| Time / evidence ID | Finding |
| --- | --- |
| 01:47 baseline | No Steam or SketchUp launch before inventory; unrelated Wine applications left running. YAWMS disabled and a stale Steam record present. |
| 01:52 loader diagnostics | Both app and prefix MSVCP140 were ARM64 in an x64 environment; loader failure before GUI. |
| 01:53 x64 runtime repair | Backed up bad DLLs and replaced only the isolated copies with the supplied x64 file. Terms/Welcome reached. |
| 07:17 user terms action | Terms were presented on the user's desktop; acceptance required explicit user authorization. This is not an installation-script action. |
| 07:34 Classic diagnostics | Graphics initialized, followed by a repeatable `SketchUp.exe+0x777a50` null access. |
| 07:36 no-Xalia experiment | Same crash; disabling accessibility helper did not fix it. |
| 07:38 DX12 comparison | Device creation succeeded; same later SketchUp fault. |
| 07:41 Windows 10 app override | Removed compatibility warning but did not fix missing-resource crash. |
| 07:43 resource repair | Read-only fault inspection identified DEFAULT_STYLE_MODEL; Styles was empty. Restoring only StyleTemplate.skp opened the modeler. |
| 07:49 content completion | Restored 481 additional missing bundled files from existing local content. |
| 07:49–07:53 initial validation | Basic line/rectangle/navigation, save/reopen and three cold starts succeeded before finalization changes. |

The historical qwindows null-theme crash is documented separately. Its trigger remains unproven and it was not reproduced in these successful sessions.

## Finalization

A complete pre-change snapshot was created, including an otherwise unsaved user model, app, prefix, GE-Proton, sniper, settings, launcher, logs and desktop/session integration. This protected the earlier working state before changes.

The app, prefix and required runtimes were relocated into a dedicated non-Steam installation. Runtime/font symlinks were rebased. A saved model opened with an empty Steam compatibility client directory; live process maps did not use old Steam paths. This established **no Steam client dependency**, while confirming GE-Proton/sniper remain required.

Steam Flatpak was removed without deleting private account data. Experiment masks/background permission records were cleared. YAWMS was enabled after stale current-session/quarantine records were moved into the rollback copy. Obsolete Wine desktop associations pointing to abandoned SketchUp prefixes were archived.

Wine prefix DPI changed from 96 to 192 without changing global GNOME scaling. Screenshots showed the enlarged UI. The launcher was rewritten to resolve its installed root, check required files and architectures, avoid duplicate processes, use one user systemd cgroup, retain diagnostic logs and raise an existing window. Apps/Dock entry matching was updated to the observed `steam_app_0` class.

A fresh-prefix reproduction exercise exposed one additional requirement: embedded Ruby rejected builtin UCRT with `unexpected ucrtbase.dll`. A native x64 UCRT restored saved-model opening. The error string was found in `x64-ucrt-ruby320.dll`; the native file was independently extracted from the cached Microsoft package with the same SHA-256. During about ten minutes of observation the modeler displayed preserved geometry using Intel hardware OpenGL and produced no dump. It closed normally, leaving the service inactive. This test is useful evidence but does not replace final physical-input and canonical GUI gates.

## Direct installation versus prefix relocation

A verified fresh prefix failed after being copied from temporary storage to the canonical root. Its app reached MakeGLContext and Wine reported an exception frame outside stack limits; no dump was created. The original canonical installation was restored immediately and reopened successfully. The fresh candidate also passed a second launch at its original path. A new installation created directly on persistent storage passed two launches. The canonical root was then rebuilt directly by the documented setup script, with the full previous canonical root preserved as rollback. This avoids the failed relocation operation. The precise internal trigger of that single migration failure remains unproven.

## Final validation and cleanup, September 28

The user explicitly approved temporary input unlocking and both exact deletion lists. All 17 approved experimental paths were checked for dependencies and removed; the item ledger records 60,566,663,168 allocated bytes. Original sources and the earlier known-good rollback were preserved. Unused workspace copies were moved reversibly into the historical rollback area. Steam client/account data were separated: the client and approved runtime experiments are removed; private account data outside the approved scope are retained.

At 192 DPI, the Welcome CEF surface initially occupied only part of the window. A prefix-local HIGHDPIAWARE registry layer fixed Qt/CEF coordinate agreement. Environment-only and Qt-variable trials did not. The original 512-pixel app icon was extracted locally for the launcher. Physical input automation was corrected to use one Wayland/uinput coordinate path; mixing X11 cursor warps with uinput clicks had produced misleading failures. These harness failures are not attributed to SketchUp. Literal Windows save paths required disabling ydotool escape interpretation.

Real touchscreen input exposed a missing Wine GetPointerFrameTouchInfo export and caused BugSplat. XInput preload filters failed real validation and were removed. A hash-guarded metadata-only alias to Wine's existing unsupported-touch function fixed the crash. It does not implement multitouch gestures. Native-call and repeated temporary-touch-device tests passed; no test device remained.

AA disabled, 2x, 4x and 8x were compared at identical native dimensions and camera. 8x was selected after edge and redraw measurements. Full physical-input regression passed, including modeling, save/reopen and window behavior. All temporary Ruby observer plugins and unused input shims were archived before the final cold launches.

Final cold launches used real GNOME Apps and pinned Dock clicks. The first two reopened the saved model, the third created a new template. Normal closes each left zero canonical-prefix processes. Dock minimize/raise and launcher cross-workspace focus retained the existing process/window. No new dumps or crash signatures appeared. The original Input Lock state (all four input classes locked) and mouse acceleration settings were restored and verified. A complete final snapshot was compared byte-for-byte, including symlink targets, with the closed installation. The original three installers retained their hashes.

YAWMS was enabled with its intended settings. Three stale Steam/old SketchUp window-map records were separately backed up and removed; unrelated mappings were retained. No active Steam session record, debug listener or experiment mask remained. The publication target is the explicitly authorized dedicated public AAG-SketchUp-Linux repository. Publication includes only reviewed support code, documentation and sanitized edge crops.

## Evidence handling

Critical hashes, architecture values, fault offsets, versions and conclusions are public documentation. Full traces, screenshots, saved models, user preferences and dumps stay private. Original source material is retained separately from production and rollback. Deleting an abandoned prefix requires confirming it is not referenced and preserving any unique user-created models first.

## Post-Golden plugin and painting work

The [plugin report](PLUGIN-MIGRATION-REPORT.md) and [painting investigation](WINDOW-PAINTING.md) retain successful, failed and invalid experiments after the original Base release. The new plugin tag leaves the original tag unchanged.
