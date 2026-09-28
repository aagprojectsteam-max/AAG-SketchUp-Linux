# Window painting regression

**Candidate and production painting regression passed on 2026-09-28.**
The original Base Golden backup and tag remain unchanged. Newly discovered defects
are recorded here; they do not silently become PASS under the old tag.

## What was reproduced

The tests use SketchUp 26.1.252, GE-Proton10-25, its private sniper runtime,
GNOME 50.1/Xwayland 24.1.10, Intel Arc/Mesa, Classic OpenGL, 8× MSAA and 192 DPI.
The prefix registry, preferences and launcher were backed up before experiments.

| Case | Before the changes |
|---|---|
| FredoCorner accessible licensing dialog | Black client area on repeated focus transitions; model remains rendered |
| Original minimal `UI::HtmlDialog` | Same focus defect, without vendor/plugin HTML |
| Ordinary SketchUp `UI.inputbox` | Six focus cycles without a black client area |
| Viewport context menu | Black first frame in all eight initial openings |
| New HTML dialog | Brief black background before CEF paints its first document |

The viewport menu is a Qt popup: `Qt691QWindowPopupDropShadowSaveBits`.
It is native SketchUp UI, but not the Win32 `#32768` menu class. The independent
HTML fixture rules out a Fredo-only cause. FredoCorner, JointPushPull and V-Ray
remain **USER_ACTION_DEFERRED**; these observations do not change licensing status.

## Findings and installed fixes

### HTML contents after focus changes

Set candidate-local `HKCU\Software\Wine\X11 Driver\ClientSideGraphics` to `N`.
Default → N → default → N tests reproduced the fault with the default setting
and removed it in two separate eight-cycle runs with N. This supports a problem
in Wine's client-side GDI surface path. The exact upstream offending change has
not been identified. This setting does not replace the modeler's OpenGL renderer.

### Qt popup first presentation

The X11 trace shows the popup mapping before the first full raster transfer,
usually by 3–5 ms. The compositor can display that initial black backing surface.
Waiting for an X11 sync before changing opacity did not reliably synchronize the
corresponding Wayland buffer.

The original [popup helper source](../scripts/popup-present.c) prepares the first
complete raster image in a pixmap, uses it as the initial window background, and
then maps the popup. The map therefore starts with painted contents. Subsequent
painting follows the application's normal path. There is no focus manipulation,
OpenGL hook, background refocus loop or compositor-wide configuration change.

Controlled evidence:

- Initial buffered prototype: six openings, zero black frames.
- Disable it with the same `ClientSideGraphics=N`: black first frame returned.
- Enable the guarded helper: twenty more openings, zero black frames.
- Menu-bar and toolbar popups: repeated candidate raster/map tests, followed by
  verified production File/Edit/View/Extensions and selection-dropdown tests.
  Discard recordings where a requested menu did not actually map.

The helper has bounded tracking and a 250 ms fallback. Unknown painting routes
map normally instead of leaving invisible windows. These fallback routes are
not evidence of clean first presentation; future validation must check them.

### Initial HTML background

New owned HTML dialogs also expose Wine's black X11 window background while CEF
prepares the document. A fixture-only white-background experiment removed the
black flash in three openings and twelve focus cycles; normal colored HTML then
rendered. Reverting the background reproduced black frames in all three openings.

The guarded version initializes the background only for captioned, non-layered
Wine dialogs with a transient Wine owner and X11 dialog window type. It does not
clear a painted document. The model window has no transient owner and is excluded.
The ordinary Win32 popup control uses style `0x94000000`, extended style `8`,
a transient Wine owner and dialog window type. It receives the same initialized
background; `GetSysColor(COLOR_MENU)` returned white on this configuration.
Xlib format-32 property values are explicitly masked to 32 bits on LP64 hosts.
The current light UI uses a white loading background. Different themes and future
window types require review rather than assuming universal compatibility.

The installed candidate repeated three HTML openings and twelve focus cycles
without a black client-area frame. LibFredo6 settings and the SketchUcation local manager each passed three
openings and twelve focus cycles. The independent Win32 popup passed six
openings without a black frame. After a cold restart through the final launcher,
six more Qt context openings passed. Production results are recorded below.

## Build, scope and rollback

Build from the original repository source while this prefix is closed:

```sh
python3 scripts/build-popup-helper.py --root "$SKETCHUP_ROOT"
```

Build prerequisites are a C compiler, `objdump`, and X11/XCB/XRender development
headers. The script does not download or install host packages. It checks x86-64
ELF architecture and the glibc symbol requirement against the validated runtime.
The compiled library and source are stored in `runtime/popup-present/`; its hash
and configuration are in `config/popup-present.json`. No compiled library needs
to be published in this repository.

[runtime-exec.py](../scripts/runtime-exec.py) validates the hash inside the private
runtime container. It sets the prefix scope and uses a library basename with
`LD_LIBRARY_PATH`, so installation paths containing spaces need no temporary link.
No `/tmp` library or global `LD_PRELOAD` setting is part of the installed solution.

For a controlled reversal, close SketchUp, restore the backed-up prefix setting
and launcher/configuration, then repeat the painting tests. Keep the original
runtime and base backup available. Do not restore vendor license state or move
old Golden tags as part of a painting rollback.

The [C integration probe](../tests/popup-present-smoke.c) tests actual first-map
pixels, 80 repeated popup lifecycles, a missing-paint timeout, unmap/destroy before
paint, excluded window styles, a mismatched prefix, and the distinction between
an owned dialog's background and its model-like owner's background.

## Rejected or invalid experiments

| Experiment | Result / disposition |
|---|---|
| `QT_QPA_PLATFORM=windows:menus=native` | SketchUp still created Qt popups; removed |
| Native Wine Wayland driver | Hardware OpenGL worked, but MSAA formats exposed 0 only; rejected; X11 and MSAA 8 restored |
| `ClientSideWithRender=N` | Two black frames in a valid six-open run; removed |
| Popup opacity until the first full transfer | One black frame in six opens; removed |
| Add `XSync` before making popup opaque | Two black frames; removed |
| `_XWAYLAND_ALLOW_COMMITS` from the application | Xwayland rejected the window-manager-only property with BadAccess and the candidate exited; removed |
| `WS_EX_COMPOSITED` on the HTML fixture | Readback did not retain the requested style; no effective A/B test or fix claimed |
| Mouse-coordinate/workspace interruptions | Excluded from acceptance counts |
| File-menu click intercepted by the GNOME Dock | Excluded; mapped View menu navigated to Edit/File with arrow keys |

No global compositor setting, host graphics setting, desktop resolution or DPI
was changed. The independent Win32 menu reproduced black first paint before its scoped
background initialization and passed six openings afterward. This control is
separate from the Qt menu result.

## Permanent acceptance gates

Run repeated tests in the candidate and again after production promotion:

- `FOCUS_LOSS_REPAINT`, `FOCUS_REGAIN_REPAINT`
- `RIGHT_CLICK_POPUP_FIRST_PAINT`, `NO_BLACK_CONTEXT_MENU_FLASH`
- `MENU_FIRST_PAINT`, `TOOLBAR_POPUP_PAINT`
- `PLUGIN_DIALOG_FIRST_PAINT`, `PLUGIN_DIALOG_FOCUS_REPAINT`
- 192 DPI/HIGHDPIAWARE, sharp UI, pointer hit testing, maximize/restore
- Classic OpenGL, Intel Arc hardware acceleration, 8× MSAA
- modeling, save/reopen, three cold launches, late-crash and clean-shutdown checks

The recordings capture the GNOME compositor output. XGetImage alone cannot prove
what appeared on the desktop. Recording requests 60 fps but produces variable-rate
damage frames; analysis uses actual frame timestamps. Raw recordings and vendor
screens remain private. A single successful repaint or launch is insufficient.

## Primary source references

- [Wine X11 configuration](https://github.com/ValveSoftware/wine/blob/proton_10.0/dlls/winex11.drv/x11drv_main.c)
- [Wine X11 drawing paths](https://github.com/ValveSoftware/wine/blob/proton_10.0/dlls/winex11.drv/graphics.c)
- [Qt 6.9 Windows integration options](https://github.com/qt/qtbase/blob/v6.9.0/src/plugins/platforms/windows/qwindowsintegration.cpp)
- [Xwayland buffer ordering, explained by a compositor maintainer](https://planet.kde.org/vlad-zahorodnii-2024-10-28-improving-xwayland-window-resizing/)
- [SketchUp HtmlDialog API and DPI behavior](https://ruby.sketchup.com/UI/HtmlDialog.html)

These sources motivated experiments. Local A/B observations determine whether
a change helps this installation. Exact Wine source inspected for the installed
GE runtime was submodule commit `7f99e78815ff702ee8585a3b19ead2c59f553cdf`.

## Validation harness corrections

Open SketchUcation through its toolbar/menu entry. Calling the vendor internal
`SCFmanager.new` directly can create the document without the normal callback
setup. The final production test used the toolbar, three close/reopen cycles,
twelve focus cycles and an actual disable/re-enable file callback afterward.
Workspaces and active windows are checked before desktop input. Interrupted
input runs and unfired keyboard accelerators are excluded from acceptance.

## Final production evidence

GNOME compositor recordings verified the installed support code and private
runtime after promotion. Whole-client black frames (>80% near-black pixels)
were absent in every valid final recording:

| Surface | Repetition | Recorded frames | Maximum black fraction |
|---|---|---:|---:|
| Viewport context menu | 20 openings | 108 | 0.0000182 |
| Original HTML dialog | 3 openings, 12 focus cycles | 206 | 0.00194 |
| LibFredo6 settings | 3 openings, 12 focus cycles | 253 | 0.000166 |
| SketchUcation via real toolbar | 3 openings, 12 focus cycles | 212 | 0.002034 |
| File/Edit/View/Extensions/selection dropdown | 3 rounds; mapped geometry verified | 95 | 0.07967 |

The maximum menu fraction includes foreground Dock overlap and text. Screens
were also inspected for readable content. File/Edit/View recordings made with
unfired Hebrew-layout accelerators were excluded. A white loading surface is
not evidence that CEF has finished loading the document. Actual callbacks and
geometry tests follow the painting checks.

All eight requested painting gates passed with 192 DPI, hardware Classic
OpenGL and 8x MSAA preserved. The installed library also passed the 80-cycle
C integration probe, timeout/cancel paths and excluded-window checks.

## Instrumented rapid-close crash and retest

One isolated candidate crashed when closed immediately after a temporary Ruby
QA timer reported readiness. It produced an access violation at
`SketchUp.exe+0x4f16b4`. The exact cause is unresolved; association with the
instrumented close does not prove the timer caused it. The dump remains private.
No such crash occurred during the long production modeling/dialog run.

The temporary timer loader was removed from both installations. Three candidate
rapid closes, followed by three final production cold launches and normal
closes, produced no new dump and left zero prefix processes. Production reached
the saved model in 10.42, 10.23 and 10.45 seconds. The last run stayed open for
30 seconds; the earlier combined production exercise lasted about 24 minutes.
These are bounded observations, not a guarantee against all future crashes.

A bundled Xalia `ReleaseChildren should not create new children` warning occurs
in both the original Base Golden and later logs. It is not a SketchUp extension
load error; the tested production session and shutdown still complete. It has
not been hidden, reclassified as a plugin failure, or fixed by disabling unrelated
runtime components.
