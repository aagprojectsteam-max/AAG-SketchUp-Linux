# Final acceptance matrix

Technical acceptance was rerun after final DPI, 8x AA, launcher, cleanup and Wine touch changes on 2026-09-28. Original source media and the previous known-good rollback remain protected. Four support-code safety tests passed, including the exact stock Wine export/idempotence integration test. Temporary GUI observers were removed before the three final cold launches.

The authoritative structured record is [acceptance.json](acceptance.json). Release publication assertions below become valid only with the published annotated tag and verified remote commit. The final release workflow verifies them before reporting completion; the commit field is the resolvable tag reference.

## Evidence

| Area | Verified result |
| --- | --- |
| UI | 192 DPI, full Welcome rendering, larger menu/toolbar/tray/dialogs, correct hits, no clipping |
| Geometry | Real Line, Delete, Rectangle and Push/Pull input; 12 edges / 6 faces |
| Mouse | Correct face/edge IDs selected; line endpoints matched requested click coordinates |
| Navigation | Real middle-drag Orbit, Shift+middle Pan and wheel Zoom; camera changes verified |
| Save/reopen | New SKP saved through GUI; all endpoint pairs and six faces preserved after close/reopen |
| Window | Maximize/restore resize native framebuffer; fullscreen request ignored |
| Apps/Dock | Actual Apps cold click; pinned Dock cold clicks; one icon; proper steam_app_0 match |
| Focus | Minimize/raise through Dock and cross-workspace launcher focus retained same processes |
| Graphics | Intel hardware OpenGL, 8x AA, native 2166x1616 framebuffer, controlled edge improvement |
| Stability | Three cold starts and normal closes; no new dump/crash signature; zero prefix processes after each |
| Touch | Repeated formerly crashing direct-touch events safely rejected; mouse remained usable |
| Cleanup | All 17 approved deletions verified absent; no extra irreversible scope; sources hash-verified |
| Session | Input Lock and pointer settings restored; YAWMS enabled and stale Steam records removed |
| Rollback | Final installation snapshot matched recursively with symlinks compared as links |

## Final cold launches

| Number | Start (local) | Interaction/observation | Processes after close |
| --- | --- | ---: | ---: |
| 1 | 2026-09-28T11:17:54.836113 | 71.96 seconds | 0 |
| 2 | 2026-09-28T11:20:42.583177 | 91.72 seconds | 0 |
| 3 | 2026-09-28T11:22:18.585750 | 194.13 seconds | 0 |

Reboot and file associations are optional and were not performed. “No stale Wine/Proton” applies to this project; unrelated live Wine applications were preserved. “No abandoned prefixes” excludes explicitly retained source/rollback archives. Steam client is absent; private remnants outside the approved deletion lists remain.

## Complete gate record

```text
ROOT_CAUSE_IDENTIFIED=PASS
ARM64_LIBRARY_ROOT_CAUSE_DOCUMENTED=PASS
MISSING_CONTENT_ROOT_CAUSE_DOCUMENTED=PASS
WORKING_INSTALLATION_BACKED_UP=PASS
CANONICAL_INSTALLATION_PATH=PASS
STEAM_DEPENDENCY=NO
STEAM_DEPENDENCY_RESOLVED=PASS
STEAM_RELAUNCH_ROOT_CAUSE_CLEANED=PASS
NO_STALE_STEAM_URI_JOBS=PASS
YAWMS_NORMAL_STATE=PASS
NO_UNNECESSARY_FLATPAK_MASKS=PASS
UI_SCALE_SIGNIFICANTLY_LARGER=PASS
MENU_SCALE=PASS
TOOLBAR_SCALE=PASS
DEFAULT_TRAY_SCALE=PASS
DIALOG_SCALE=PASS
MOUSE_HIT_TEST=PASS
NO_POINTER_OFFSET=PASS
NO_UI_CLIPPING=PASS
VIEWPORT_GEOMETRY=PASS
MAXIMIZE_AFTER_SCALING=PASS
APPS_LAUNCH=PASS
DOCK_LAUNCH=PASS
DOCK_FOCUS_EXISTING=PASS
NO_DUPLICATE_DOCK_ICON=PASS
CORRECT_ICON=PASS
CORRECT_WINDOW_MATCHING=PASS
NO_TERMINAL_REQUIRED=PASS
CREATE_NEW_MODEL=PASS
LINE_TOOL=PASS
RECTANGLE_TOOL=PASS
PUSH_PULL=PASS
SELECTION=PASS
ORBIT=PASS
PAN=PASS
ZOOM=PASS
SAVE_SKP=PASS
CLOSE_CLEANLY=PASS
REOPEN_SAVED_SKP=PASS
GEOMETRY_PRESERVED=PASS
MAXIMIZE=PASS
COLD_RELAUNCH_1=PASS
COLD_RELAUNCH_2=PASS
COLD_RELAUNCH_3=PASS
NO_NEW_BUGSPLAT=PASS
NO_LATE_CRASH=PASS
NO_STALE_RUNTIME_PROCESSES=PASS
NO_ABANDONED_PREFIXES=PASS
NO_STALE_STEAM=PASS
NO_STALE_WINE_PROTON=PASS
NO_STALE_TEST_JOBS=PASS
NO_OBSOLETE_AUTOSTART=PASS
NO_DUPLICATE_LAUNCHERS=PASS
NO_DEBUG_PORTS_LEFT_ENABLED=PASS
NO_UNNECESSARY_MASKS=PASS
ORIGINAL_INSTALL_MEDIA_PRESERVED=PASS
REAL_WINDOWS_INSTALL_UNTOUCHED=PASS
INSTALL_DOCUMENTATION=PASS
ROOT_CAUSE_DOCUMENTATION=PASS
TROUBLESHOOTING_DOCUMENTATION=PASS
ROLLBACK_DOCUMENTATION=PASS
SECRETS_SCAN=PASS
PROPRIETARY_BINARY_SCAN=PASS
GITHUB_COMMIT=stable-sketchup-2026-ubuntu-final^{commit}
GITHUB_TAG=stable-sketchup-2026-ubuntu-final
GITHUB_PUSH=PASS
TAG_PUSH=PASS
WORKTREE_CLEAN=YES
FINAL_GOLDEN=YES
DISK_CLEANUP_AUDIT=PASS
HARDWARE_ACCELERATION_STATUS=Intel Arc MTL; Classic OpenGL 4.6; Mesa 26.0.8; live final launch and renderD128 verified
VIEWPORT_RESPONSIVENESS=PASS
ORBIT_SMOOTHNESS=PASS
PAN_SMOOTHNESS=PASS
ZOOM_SMOOTHNESS=PASS
UI_RESPONSIVENESS=PASS
SKP_FILE_ASSOCIATION=NOT_REQUIRED
REBOOT_TEST=NOT_RUN
PERSISTENT_CONFIGURATION=PASS
FINAL_RENDERER_IDENTIFIED=PASS
FINAL_GPU_IDENTIFIED=PASS
HARDWARE_ACCELERATION=PASS
NATIVE_VIEWPORT_RESOLUTION=PASS
ANTI_ALIASING_ENABLED=PASS
DIAGONAL_EDGE_SMOOTHNESS=PASS
MODEL_EDGE_QUALITY=PASS
AXIS_LINE_QUALITY=PASS
TEXT_AND_UI_SHARPNESS=PASS
NO_VIEWPORT_BLUR=PASS
NO_RENDERER_REGRESSION=PASS
LAUNCH_FROM_COLD_STATE=PASS
MODELING_VIEW_VISIBLE=PASS
DELETE_TOOL=PASS
WINDOW_RESTORE=PASS
INPUT_LOCK_RESTORED=PASS
POINTER_SETTINGS_RESTORED=PASS
TOUCH_CRASH_REGRESSION=PASS
FINAL_BACKUP_VERIFIED=PASS
SOFTWARE_RENDERING_FALLBACK=NO
FULLSCREEN=NOT_SUPPORTED_BY_TESTED_WINDOW_MANAGER_REQUEST
```
