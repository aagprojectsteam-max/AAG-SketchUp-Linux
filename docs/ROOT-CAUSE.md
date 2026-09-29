# Root causes and evidence

The application tested is SketchUp **26.1.252 x86-64**. Paths below use `$SKETCHUP_ROOT` for the canonical Linux installation and `$STEAM_DATA` for the historical Steam data directory. No Windows partition was modified. No SketchUp executable was patched.

## Confirmed root cause: ARM64 MSVCP140.dll in an x64 process

Two historical files were wrong:

- `$STEAM_DATA/steamapps/common/AAG-SketchUp-2026/msvcp140.dll`
- `$STEAM_DATA/steamapps/compatdata/<historical-app-id>/pfx/drive_c/windows/system32/msvcp140.dll`

Both were ARM64 (PE Machine `0xaa64`), version **14.29.30157**. SketchUp is x86-64 (`0x8664`). The fresh loader trace reported `c000007b` for MSVCP140, followed by `c0000135` for dependent modules, and exit status 53 before the UI appeared. An x64 process cannot load an ARM64 PE module as its native runtime.

The files were already wrong when this investigation audited them. The available evidence cannot distinguish installer behavior, an earlier manual copy, or another experiment as their source. Wine did not convert their architecture. Attribution to a particular installer would be speculation.

The repair replaced both copies **in an isolated Linux test installation**, after backup, with the x64 MSVCP140 already present in the user-supplied application directory. The replacement is **14.51.36247.0**, 643,512 bytes. It allowed the application to reach the terms and Welcome screens. Terms acceptance was a separate, explicitly authorized user action.

| File | SHA-256 |
| --- | --- |
| Incorrect ARM64 MSVCP140 | `dfb0e03a4e9979ecd6332ad9d7325a562fb68a01a798fd88109421d23d34b853` |
| Correct x64 MSVCP140 | `7c26614e1d733892c2deac7e245ce115504b1d80592dd0a01b08e3e5a55f89ca` |
| Unmodified SketchUp.exe | `f70f1c6561115d652275014dedf0ba067b59e910e6d93971c8dfabaffbc92354` |

## Confirmed root cause: missing StyleTemplate.skp

After the DLL repair, creating a model crashed at `SketchUp.exe+0x777a50`, reading address `0x1a0` through a null pointer. The fault happened with both Classic/OpenGL and New/DX12 after graphics initialization.

Read-only inspection of the calling code found `DEFAULT_STYLE_MODEL`. The application's `Support/SketchUp.dat` resolves that name to `StyleTemplate`; the resource lookup uses the Styles directory. That directory was empty in the affected prefix. The failed model load left a null object in the style thumbnail path.

Required destination:

```text
$SKETCHUP_ROOT/compatdata/pfx/drive_c/ProgramData/SketchUp/SketchUp 2026/SketchUp/Styles/StyleTemplate.skp
```

Restoring **only this file** removed the repeated modeler crash. It was recovered from an existing local extraction of the user's SketchUp 26.2 installation material. Its internal model format version is 21.0.0; size 49,235 bytes; SHA-256:

```text
30e2b7348a606956b6f8baadfb79ed07a05947724135839ac1bac7db7611f141
```

The first successful session recorded Rectangle, Draw Line and File Save operations. A further 481 bundled files were then restored: Styles, Materials, Components, Environments, HatchPatterns, Workspaces and Tutorials. Existing files were preserved. The executable stayed **26.1.252**. This is a tested mixed provenance content restoration, not a claim that a full 26.2 application was validated.

The immediate fault is confirmed by the single-file repair. Why the earlier installation omitted ProgramData content is not proven: manually assembled or partially extracted application trees are a plausible explanation, but no complete installer trace establishes responsibility.

## Confirmed prerequisite: native x64 UCRT for embedded Ruby

A newly created GE-Proton10-25 prefix, supplied with the app, content and correct MSVCP140, exited shortly after opening a model with `unexpected ucrtbase.dll`. The literal error string is in the supplied `x64-ucrt-ruby320.dll`. The working older prefix already contained a native Microsoft UCRT.

Copying the native x64 file into `drive_c/windows/system32/ucrtbase.dll`, with `HKCU\Software\Wine\DllOverrides` value `ucrtbase="native,builtin"`, allowed the fresh prefix to open and display saved geometry. An Xalia exception printed during the failed process teardown; it is not evidence that Xalia caused this startup failure.

Verified prerequisite:

- UCRT version **10.0.10586.15**, 986,504 bytes, x86-64.
- DLL SHA-256: `51cbbde17a768930300236facd9738f54b7801e6715771ff8af90bfbe3fad44f`.
- Exact file independently extracted from the already cached Microsoft `VC_redist.x64.exe` used by Winetricks `ucrtbase2019`.
- Package SHA-256: `52b196bbe9016488c735e7b41805b651261ffa5d7aa86eb6a1d0095be83687b2`.
- Extraction is `cabextract -F a10`, followed by `cabextract -F ucrtbase.dll` on that cabinet. No Windows installer needs to run for this extraction.

The [Winetricks 20250102 source](https://raw.githubusercontent.com/Winetricks/winetricks/20250102/src/winetricks) supplies that package and extraction method. The local extraction and hash comparison establish the provenance of the tested file.

## Failed experiments and their limits

| Experiment | Observed result | What it establishes |
| --- | --- | --- |
| System Wine / Wine 11 | Earlier modeler or UI failures | These historical configurations were not validated with all later repairs. |
| GE-Proton11-7 | Checksum-verified runtime; still failed historical modeler tests | A runtime upgrade alone did not repair missing content or mismatched DLLs. |
| Direct Proton and UMU | Several early launch/renderer failures | No evidence that UMU is required by the final launcher. |
| Steam with repaired sniper | Welcome and farther startup, still BugSplat | A complete runtime helped execution but did not fix the application faults. |
| Classic graphics | Historical WGL/pixel-format errors; later GL initialization succeeded before the same null access | WGL failure is not the confirmed cause of the later style-template crash. |
| DX12 | `ID3D12Device` creation succeeded, followed by the same style-template null access | Device creation alone is not successful modeling; switching API did not fix missing content. |
| Disable Xalia | Same content-related crash | Not the repair. Final tests use default Xalia behavior. |
| Report Windows 10 | Same content-related crash; compatibility warning removed | Useful app-specific compatibility setting, not the crash repair. |
| Virtual desktop, llvmpipe, Zink, alternate antialiasing | No complete stable modeling result in preserved historical tests | None is established as necessary. Software rendering is not the chosen path. |
| VC++, MFC, .NET, DirectX and UIAutomation experiments | Dependencies accumulated in old prefixes | Do not install the historical list blindly; the fresh-prefix procedure tests a smaller set. |

## Secondary issues

### Historical Qt crash

An earlier minidump identifies `qwindows.dll` RVA `0x5c2b7` (BugSplat section offset `0x5b2b7`), near a null `QWindowsTheme::instance()` access during window creation. The [Qt 6.9.1 source](https://raw.githubusercontent.com/qt/qtbase/v6.9.1/src/plugins/platforms/windows/qwindowswindow.cpp) contains that call. The original trigger is unproven; it did not recur in the later validated sessions. It is distinct from the MSVCP loader failure and the SketchUp style-thumbnail crash.

### Welcome/CEF

A working Welcome screen proves only that the CEF startup path worked. It does not validate the modeler. `SU_CEF_DISABLE_GPU=1` is scoped to CEF; the modeling viewport still uses hardware OpenGL. Debugging used CEF remote ports 9222, 9224 and 9226; the production launcher unsets that setting.

### Steam reopening

Historical delayed debugging jobs repeatedly invoked a Steam game URI. YAWMS also retained a Steam window in its saved current session. Flatpak masks, background restrictions and disabling YAWMS were temporary mitigations. Cleanup must remove the launch triggers and restore normal session management; masks alone do not remove the cause.

### Prefix relocation during finalization

A fresh candidate worked at its creation path but exited after a copy to the canonical path, with Wine reporting an exception frame outside stack limits. Critical DLL/content hashes remained correct. The previous production state was restored and worked. The unchanged candidate also worked again at its original path. Creating a fresh installation directly on persistent storage succeeded, so the setup procedure creates a prefix at its final path and rollback restores that same path. The exact relocation trigger remains unproven; it is not attributed to the ARM64 or style-content faults.

## Runtime and graphics conclusion

The relocated application opened a model while its Steam compatibility client directory was empty and the Steam client was absent. Live process maps and environment were inspected for old Steam paths. **Steam client dependency: NO.** The required standalone components remain **GE-Proton10-25** and **Steam Linux Runtime 3.0 sniper**, stored under the canonical installation.

Classic/OpenGL is the selected modeler path on Intel Arc/Mesa. Native Wine DPI is set to 192 in the isolated prefix. Final GUI, performance and cleanup acceptance are tracked separately in [TEST-MATRIX.md](TEST-MATRIX.md); this root-cause document does not imply those gates have passed.

## Confirmed touch API crash

Real direct-touch events reached Qt 6.9.1, which called `USER32.GetPointerFrameTouchInfo`. GE-Proton10-25 Wine exported related pointer functions but omitted this one. Wine's generated missing-function stub aborted the process and caused BugSplat. A temporary Linux uinput direct-touch device reproduced this failure independently of mouse clicks. [Qt's pointer handler](https://raw.githubusercontent.com/qt/qtbase/v6.9.1/src/plugins/platforms/windows/qwindowspointerhandler.cpp) returns normally when that API reports unsupported input.

The original support script `patch-wine-touch.py` adds the missing export as an alias of Wine's existing same-signature `GetPointerTouchInfoHistory`. In this exact build that function returns FALSE and sets Win32 error 120 (`ERROR_CALL_NOT_IMPLEMENTED`). All original exports, ordinals, function RVAs and executable sections remain unchanged. Only export-name metadata is extended in a new read-only PE section. This is a compatibility fallback, not an implementation of multitouch gestures.

The script requires exact stock Wine SHA-256 `996d515d8cb4828cd0a61fc82414e15ebf352e49d1d3655ca9dd0e4cbc29d7a1`; the patched hash is `4e1251c8074cef40260caf36a9c84db42be33400af88a15c39fa5f638c42df65`. Both copies are backed up before writing. No SketchUp or Microsoft executable is patched. A compiled local Win32 call returned FALSE/error 120/unchanged count and exit 0. Repeated direct-touch injections no longer crashed the modeler; mouse selection worked afterwards.

Earlier LD_PRELOAD trials attempted to suppress XInput extension discovery or touch cookies. The broad trial was associated with a hang; narrow XGetEventData/dlsym filters passed isolated tests but did not stop the real touch crash. They were removed from the production launcher and active configuration. Their evidence stays private. The exact bypass mechanism is unproven.

## Confirmed DPI disagreement

At Wine DPI 192, Welcome initially painted content in only part of its window and showed black unused space. Qt high-DPI environment trials and the environment-only `__COMPAT_LAYER` did not fix it. Setting the default value of the private prefix's `AppCompatFlags\Layers` key to `HIGHDPIAWARE` fixed full-window CEF rendering and template hit-testing. Native menu, toolbar, tray and dialog metrics remained enlarged. Ruby's view API reported 1083×808 logical pixels and 2166×1616 physical pixels; a framebuffer capture matched the latter. Global GNOME scaling was unchanged.

## Final antialiasing comparison

Classic OpenGL's GUI offers disabled, 2×, 4×, 8× and 16× AA. Controlled captures tested disabled, 2×, 4× and 8× at the same camera, geometry, window and DPI. Intermediate edge coverage increased while flat interiors remained unchanged. 8× was selected after near-equal redraw timing versus 4× on the simple model. The old AAMethod=0 setting is not part of the final configuration. Detailed measurements and limitations are in [GRAPHICS.md](GRAPHICS.md).

## Black dialogs and first-frame popup flash

Post-Golden regression found two distinct paths: retained HTML client contents
after focus changes, and an X11 window mapped with an uninitialized black
background before its first raster paint. Candidate A/B tests support a
prefix-local `ClientSideGraphics=N` setting plus an original, guarded raster
presentation helper. See [the evidence and rejected experiments](WINDOW-PAINTING.md).
Do not reduce DPI/MSAA, enable a software modeler or globally change the compositor.
The exact upstream change causing the retained HTML defect remains unproven.

## Version metadata used by future audits

The tested SketchUp executable has fixed PE version 26.0.0.0 and bounded StringFileInfo build 26.1.252. Update comparison now preserves both and uses the unambiguous string build; filename or fixed header alone would misidentify patch releases. See [UPDATE.md](UPDATE.md).

## General network trust integration

The host's CA-bundle path was missing inside the actual container. DNS still
worked; inspected HTTPS chains failed. Supplying the existing host bundle fixed
container TLS and the controlled WinHTTP/WinINet test without weakening validation.
SketchUp then independently reset embedded Ruby's SSL_CERT_FILE to its vendor
bundle; a prefix-local bootstrap repaired Ruby's default store. See the complete
[network comparison, callback and failed-experiment record](NETWORKING.md).
No application binary or vendor CA file was patched for networking.

## Post-Golden Hebrew input, 2026-09-29

A native Wayland application received Hebrew while Xwayland GTK and a plain Wine EDIT received Latin under the same Hebrew IBus engine. Xwayland had only the US map. Changing that map to the existing GNOME US/Hebrew pair fixed the same running Wine process; restoring the old map reproduced failure. The origin of the divergence is unknown. A guarded launcher helper restores the existing bilingual map and active group. [Evidence and boundaries](HEBREW-INPUT.md).
