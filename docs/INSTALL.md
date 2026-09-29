# Reproduce the isolated installation

This procedure starts with complete, legitimate **user-supplied application and content files**. It does not download SketchUp, modify a real Windows installation, accept terms, or activate a license. A bootstrap installer alone is not the input accepted by this script: preserve/extract its complete payload first, or use read-only copies of the application's installed files.

## 1. Prerequisites

The tested host is Ubuntu 26.04.1 x86-64, GNOME 50.1 on Wayland/Xwayland, Intel Arc MTL and Mesa 26.0.8. Use a local graphical login with a working user systemd manager. The runtime uses unprivileged container execution; host policy must permit pressure-vessel/bubblewrap.

Required host commands/packages:

```bash
sudo apt install python3 coreutils systemd bubblewrap wmctrl \
  desktop-file-utils xdg-user-dirs libglib2.0-bin libnotify-bin \
  fontconfig fonts-liberation icoutils
```

`cabextract` is needed for the optional UCRT extraction below; `mesa-utils` and `vulkan-tools` are useful for diagnosis. Observed package versions were Python 3.14.3, bubblewrap 0.11.1, wmctrl 1.07 and fonts-liberation 2.1.5. System Wine, winetricks, Steam, UMU and .NET installation are not steps in the fresh-prefix recipe.

Allow about 6 GB for the installation, plus source files and a rollback copy. Storage varies with source content and caches. Keep the destination on a persistent filesystem supporting Unix permissions and symlinks, outside `/tmp`. Create the prefix directly at that final path. A tested prefix copied from a temporary path failed once during startup; rebuilding directly at the permanent path avoided that failure. Restore backups to their original path instead of moving a live installation to a new location.

## 2. Supply exact runtime directories

Obtain and extract:

- [GE-Proton10-25 release](https://github.com/GloriousEggroll/proton-ge-custom/releases/tag/GE-Proton10-25). Verify the upstream archive checksum. The extracted directory must contain `proton`, `files/` and `version`.
- [Valve sniper snapshot 3.0.20260805.254768](https://repo.steampowered.com/steamrt-images-sniper/snapshots/3.0.20260805.254768/). Obtain `SteamLinuxRuntime_sniper.tar.xz` and verify its entry in the upstream `SHA256SUMS`. Use the complete extracted `SteamLinuxRuntime_sniper` directory, including `_v2-entry-point`, pressure-vessel and the platform payload.

The tested sniper `VERSIONS.txt` identifies depot/sniper `3.0.20260805.254768` and pressure-vessel `0.20260805.0`. The tested Proton version file reads `1762104463 GE-Proton10-25`; its Wine binary reports `wine-10.0 (Staging)`. These are independent local runtime directories. Steam installation or login is unnecessary for the launcher.

## 3. Supply legitimate SketchUp and Microsoft files

Prepare these source paths:

| Input | Required contents |
| --- | --- |
| Application directory | Complete SketchUp 26.1.252 x64 tree: SketchUp.exe, its DLLs, Tools, Support, CEF, Welcome assets and remaining application files |
| ProgramData content directory | Contents of `ProgramData/SketchUp/SketchUp 2026/SketchUp`, including `Styles/StyleTemplate.skp` and bundled content |
| `msvcp140.dll` | Legitimate native x64 14.51.36247.0 file already supplied with the tested app |
| `ucrtbase.dll` | Legitimate native x64 10.0.10586.15 file, obtained as below or from the user's matching installed runtime |

The tested content was recovered from the user's **existing 26.2** media extraction, while the executable remained **26.1.252**. No new SketchUp installer was downloaded. The tested `StyleTemplate.skp` has internal model version 21.0.0. Do not replace an application with a different release and assume the same validation applies.

Expected critical SHA-256 values:

```text
f70f1c6561115d652275014dedf0ba067b59e910e6d93971c8dfabaffbc92354  SketchUp.exe
7c26614e1d733892c2deac7e245ce115504b1d80592dd0a01b08e3e5a55f89ca  msvcp140.dll
51cbbde17a768930300236facd9738f54b7801e6715771ff8af90bfbe3fad44f  ucrtbase.dll
30e2b7348a606956b6f8baadfb79ed07a05947724135839ac1bac7db7611f141  Styles/StyleTemplate.skp
```

### Extract the tested UCRT without running its installer

The verified Microsoft package is the x64 package referenced by Winetricks 20250102 `ucrtbase2019`:

[Microsoft VC_redist.x64.exe](https://download.visualstudio.microsoft.com/download/pr/85d47aa9-69ae-4162-8300-e6b7e4bf3cf3/52B196BBE9016488C735E7B41805B651261FFA5D7AA86EB6A1D0095BE83687B2/VC_redist.x64.exe).

Package SHA-256: `52b196bbe9016488c735e7b41805b651261ffa5d7aa86eb6a1d0095be83687b2`.

Using your already obtained legitimate package:

```bash
sudo apt install cabextract
UCRT_SOURCE="$HOME/SketchUp-sources/VC_redist.x64.exe"
UCRT_OUTPUT="$HOME/SketchUp-sources/ucrt-x64"
mkdir -p "$UCRT_OUTPUT"
sha256sum "$UCRT_SOURCE"  # Compare with the package hash above before extraction.
cabextract -q -d "$UCRT_OUTPUT" -F a10 "$UCRT_SOURCE"
cabextract -q -d "$UCRT_OUTPUT" -F ucrtbase.dll "$UCRT_OUTPUT/a10"
sha256sum "$UCRT_OUTPUT/ucrtbase.dll"
file "$UCRT_OUTPUT/ucrtbase.dll"
```

Expect PE32+ x86-64 and the DLL hash above. ARM64 and x86 files cannot substitute for this x64 file. No proprietary file is included in this repository.

## 4. Create a new installation

Set paths to your real source directories; the following are placeholders:

```bash
PROJECT_ROOT="$HOME/src/AAG-SketchUp-Linux"
SKETCHUP_ROOT="$HOME/Applications/SketchUp2026"
SKETCHUP_SOURCES="$HOME/SketchUp-sources"

python3 "$PROJECT_ROOT/scripts/prepare-installation.py" \
  --root "$SKETCHUP_ROOT" \
  --app-source "$SKETCHUP_SOURCES/application-26.1" \
  --content-source "$SKETCHUP_SOURCES/programdata-content" \
  --msvcp-x64 "$SKETCHUP_SOURCES/application-26.1/msvcp140.dll" \
  --ucrt-x64 "$SKETCHUP_SOURCES/ucrt-x64/ucrtbase.dll" \
  --proton-source "$SKETCHUP_SOURCES/GE-Proton10-25" \
  --container-source "$SKETCHUP_SOURCES/SteamLinuxRuntime_sniper" \
  --dpi 192
```

The destination must not exist. Setup copies all inputs, initializes a fresh Proton prefix by running `cmd.exe /c exit 0` inside sniper, installs the required content/DLLs, records input hashes and validates x64 architecture. It never edits the source directories. If initialization fails, inspect `logs/setup/prefix-init.log`; preserve that failed destination for diagnosis and retry only after understanding the failure.

Before prefix creation, setup runs `patch-wine-touch.py` on the **private Wine user32.dll**. It accepts only stock SHA-256 `996d515d8cb4828cd0a61fc82414e15ebf352e49d1d3655ca9dd0e4cbc29d7a1`, preserves a `.aag-original` backup, and adds one export alias with no executable code changes. The resulting hash is `4e1251c8074cef40260caf36a9c84db42be33400af88a15c39fa5f638c42df65`. The launcher checks both runtime and prefix DLLs. Other Proton builds are deliberately rejected. See [the touch compatibility analysis](ROOT-CAUSE.md#confirmed-touch-api-crash).

Settings applied:

```text
HKCU\Control Panel\Desktop
  LogPixels = DWORD 192 (0x000000c0)
HKCU\Software\Wine\AppDefaults\SketchUp.exe
  Version = "win10"
HKCU\Software\Wine\DllOverrides
  ucrtbase = "native,builtin"
HKCU\Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers
  (Default) = "HIGHDPIAWARE"
```

GE-Proton supplies additional default DLL settings itself; these are not a request to reproduce every old experimental override. The native MSVCP file is copied to both the application directory and prefix System32.

`PrivatePreferences.json`, under the prefix user's Local AppData SketchUp directory, selects Classic graphics:

```json
{
  "This Computer Only": {
    "Preferences": {
      "UseNewRenderer": false,
      "TryNewRenderer": false,
      "CountOfNewRenderersOnProbation": 0,
      "AAMethod": 8,
      "UseFastFeedback": false,
      "ValidateGraphicsCardPrefs": true
    }
  }
}
```

192 DPI doubles Wine UI metrics relative to the initial 96 DPI setup. The prefix-local HIGHDPIAWARE layer makes Qt and CEF agree on scaling. GNOME remains at its existing 2× scale. Classic OpenGL uses 8× MSAA with fast feedback disabled; the native framebuffer remains 2166×1616 pixels in the tested maximized layout. See [graphics validation](GRAPHICS.md).

The script does not write `AcceptedTerms`. Review and accept terms personally if shown; provide your own license credentials through SketchUp's normal flow. Cloud and licensing flows were not independently validated for another account.

## 5. Validate, launch and install desktop integration

```bash
"$SKETCHUP_ROOT/bin/launch-sketchup.py" --check
"$SKETCHUP_ROOT/bin/launch-sketchup.py"
```

The check should return `required_files: PASS`. The launcher uses a user systemd service named `aag-sketchup-2026.service`, with no restart loop or session time limit. It only operates on this installation's runtime processes. Its normal output is stored under `logs/`.

Once the modeling window works:

```bash
python3 "$SKETCHUP_ROOT/bin/install-launcher.py" --root "$SKETCHUP_ROOT" --desktop-shortcut
```

Open GNOME Apps, search **SketchUp 2026**, launch it and pin that entry to the Dock. The desktop file uses `StartupWMClass=steam_app_0`, matching the actual window class with the launcher's app ID zero. The installer extracts the original 512-pixel application icon from your local SketchUp.exe with icoutils. No proprietary icon is distributed here. Desktop files replaced by the helper are backed up beneath `backups/desktop-*`.

## 6. Verify the complete result

Test a new model, line, rectangle, push/pull, selection/deletion, orbit/pan/zoom, tray, menus and a dialog. Save to a new SKP file, close normally and reopen it. Verify geometry. Test maximize/restore, Apps and Dock launch, focus existing, and three cold starts. Look for clipped controls or pointer offsets at 192 DPI.

```bash
"$SKETCHUP_ROOT/bin/collect-diagnostics.py"
"$SKETCHUP_ROOT/bin/launch-sketchup.py" --debug
systemctl --user status aag-sketchup-2026.service
```

A closed application should leave no processes for its prefix. Other Wine applications may legitimately remain running. Use [the acceptance matrix](TEST-MATRIX.md) and [troubleshooting](TROUBLESHOOTING.md). Reboot/logout is optional only after saving all work; the installed paths and desktop files must be persistent.

## Popup painting support

The current support build also needs a C compiler, binutils and X11/XCB/XRender
development headers (`build-essential binutils libx11-dev libxcb1-dev libxrender-dev`
on Ubuntu). Preparation builds the original local popup helper; no vendor
DLL is modified for this fix. See [window painting](WINDOW-PAINTING.md) for scope, tests and rollback.

## Host trust and account setup

The launcher copies the existing host CA bundle into its private `config/network/`
directory and supplies it to the container and Wine. The installer also places
`000_AAG_HostTrust.rb` in this prefix's SketchUp 2026 Plugins directory to account
for SketchUp resetting Ruby's certificate path. Original helper sources are in
this repository; certificates, credentials and session data are not.

A missing or invalid explicitly configured `SSL_CERT_FILE` stops preparation of
network trust. Correct the host configuration; do not fall back to disabled TLS.
Restart after a host trust change. Sign in personally using the normal default
browser, then check SketchUp's account menu and a clean relaunch. See
[NETWORKING.md](NETWORKING.md) for exact tested APIs, callback behavior and limits.
