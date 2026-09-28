# Change log

## 20260928-014754
- Read handoff and audited live system without launching SketchUp/Steam.
- Wrote baseline and path selection.
- Created isolated copies from existing Linux-side Steam prefix/application; originals preserved.

- Built tracked, time-limited diagnostic services with logs, full process-group cleanup, and window capture.
- Corrected runner lifetime/standalone mode after two runner-level failures; no Steam client launched.
- Confirmed ARM64 MSVCP140.dll in both the existing Steam app and prefix; replaced only the diagnostic copies with existing x64 14.51.36247.0.
- Reached Trimble Offering Terms; requested user's decision without accepting it or changing AcceptedTerms.
- Located historical qwindows null dereference in theme/window creation code. Further modeling reproduction remains pending the terms decision.

- User explicitly authorized Accept; terms accepted through the UI.
- Fresh classic-renderer model creation crashes at SketchUp+0x777a50, RCX=0, reading +0x1a0. WGL contexts and shader initialization succeed before crash.
- Disabling Xalia reproduces identical crash; setting not retained.
- Testing new-renderer A/B in the same prefix, with preference backup.

## 2026-09-28 07:43 — modeler crash localized to missing style resource

New renderer and Windows 10 app compatibility reproduce the same SketchUp+0x777a50 null dereference. Both experiments reverted. Read-only inspection of the calling code identifies DEFAULT_STYLE_MODEL (Support/SketchUp.dat -> StyleTemplate) and Styles path. Isolated ProgramData Styles was empty. Copied only StyleTemplate.skp from existing 26.2 MSI test data (model header21.0.0); provenance/hash in logs/style-template-restoration.json. Verification in progress.

## 2026-09-28 07:55 — initial validation before finalization

StyleTemplate restoration removed the reproducible modeler crash. Rectangle/line UI commits, camera navigation and SKP save passed. Remaining bundled content restored from existing local MSI data; Windows10 per-app compatibility retained to remove warning. Three final-configuration cold launches and normal closes passed without fresh dumps. Launcher installed with backup, duplicate-click behavior verified, and final installed-launcher session left intentionally open. Final source DLL hash remains unchanged. Reports and configuration snapshot updated.

## 2026-09-28 — finalization baseline

Preserved a full rollback and original media; relocated runtime out of Steam; removed Steam client/masks/background workaround; restored YAWMS. Applied prefix-only 192 DPI and added portable setup/launcher/diagnostics. Identified the native UCRT prerequisite and verified its cached source package. Direct fresh-prefix creation on persistent storage passed model opening; a failed copied-prefix migration was rolled back and documented. At that point, physical-input and cleanup decisions were pending; the completed results are below.

## 2026-09-28 — final validated configuration

- Completed both approved deletion lists and retained original sources and protected rollback.
- Fixed Qt/CEF DPI agreement at 192 DPI and installed the original local app icon.
- Added a guarded Wine missing-touch-export fallback after a reproduced direct-touch crash; removed failed preload trials.
- Selected 8x Classic MSAA using controlled native captures and redraw measurements.
- Passed actual mouse modeling, save/reopen, Apps/Dock/focus, window restore/maximize and three final cold launches.
- Restored Input Lock, pointer settings and YAWMS functionality; archived temporary probes and stale mappings.
- Created and verified the final rollback snapshot; prepared a sanitized, reproducible public release.

## Plugin Golden — 2026-09-28

Add four reviewed extension groups and scoped first-paint/focus repairs, with repeated GUI/function regression. Add audited migration tools, metadata and a verified independent plugin backup. See [release report](PLUGIN-MIGRATION-REPORT.md).
