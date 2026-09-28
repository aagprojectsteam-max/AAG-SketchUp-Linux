# Uninstall and rollback

All operations here are scoped to the Linux SketchUp installation. Original media, the real Windows installation, other Wine prefixes and unrelated GNOME preferences should remain untouched.

## Before either operation

1. Save your models outside the installation root. Include any recovery/autosave files stored in the prefix.
2. Close SketchUp normally. Confirm `systemctl --user is-active aag-sketchup-2026.service` reports inactive or the transient unit has been collected.
3. Confirm no process still uses this exact compatibility-data directory. The diagnostic collector reports `prefix_process_count`. Never stop all Wine processes globally.
4. Record the installation root, desktop files and backup location. Do not infer a path from an old experiment's name.

## Make a complete rollback copy

Choose a new private destination on persistent storage, with SketchUp closed:

```bash
SKETCHUP_ROOT="$HOME/Applications/SketchUp2026"
SKETCHUP_BACKUP="$HOME/Backups/SketchUp2026-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$SKETCHUP_BACKUP"
cp -a --reflink=auto "$SKETCHUP_ROOT" "$SKETCHUP_BACKUP/installation"
cp -a "$HOME/.local/share/applications/aag-sketchup-2026.desktop" "$SKETCHUP_BACKUP/"
```

Also preserve the optional desktop shortcut and your original application/content/media directories. The full installation copy includes the prefix registry, SketchUp preferences, app, dependencies, runtime, scripts and local logs. It may include private account information; never publish it. Verify critical file hashes and that the copied runtime files can be read before relying on the backup.

The investigation's pre-finalization snapshot additionally includes the user's previously unsaved model, launcher files, launch environment, process mapping and YAWMS configuration. Its exact local location is recorded in the private finalization state file. It is retained until a final validated replacement snapshot exists.

## Restore after a failed change

With the application closed, rename the broken installation to a clearly marked recovery directory. Copy the backed-up installation into **the original canonical path**, preserving symlinks and permissions. Restore only SketchUp's desktop entry, or run the restored `bin/install-launcher.py --root <canonical-root>` to regenerate it. Restoring to the same path avoids stale absolute runtime/font links in existing prefixes.

Run the restored launcher with `--check`, open a known saved model, verify geometry and close. Then test a cold Apps/Dock launch. Keep the failed copy until any models created since the backup have been recovered. A prefix contains application state, so do not discard it merely because it no longer launches.

## Remove the installation

Unpin SketchUp from the Dock using its normal context menu. Remove only these installed integration files, if they belong to this installation:

```text
$HOME/.local/share/applications/aag-sketchup-2026.desktop
<user desktop directory>/SketchUp 2026.desktop
```

Refresh with `update-desktop-database "$HOME/.local/share/applications"`. The installer preserves previous desktop entries under `$SKETCHUP_ROOT/backups/desktop-*`; restore a previous one only if you intentionally want that older installation.

After recovering models and verifying the backup, remove the **exact canonical root**. That removes app, prefix, private runtimes, scoped font configuration, launch scripts and logs together. There is no persistent service to uninstall: `systemd-run --collect` creates a transient user unit at launch. Do not remove original source/media directories or shared host packages merely because SketchUp used them.

The project does not install a global Wine configuration, global environment variables, GNOME scaling change or required SKP file association. There is consequently no global setting to undo for those items.

## YAWMS and Steam cleanup

YAWMS was enabled again after stale Steam session records were moved into the private rollback snapshot. Its unrelated settings were preserved. At the finalization baseline these settings were:

```text
enable-autoclose-session=true
enable-restore-previous-session=false
enable-autorestore-sessions=false
stash-and-restore-states=true
```

Use the extension's preferences to restore a setting only if it was changed subsequently. Do not overwrite the user's whole current YAWMS configuration with an old snapshot: that could replace unrelated saved sessions. Restoring the quarantined Steam entries can recreate the unwanted relaunch, so inspect them individually first.

Steam Flatpak was uninstalled without deleting account data; experiment-specific masks and background blocks were removed. The final SketchUp runtime does not require reinstalling Steam. Account data is private and is not part of this repository. The cleanup ledger distinguishes remaining private data from obsolete runtime copies.

## Final validated snapshot

The private project stores the verified final installation at `backups/final-golden-20260928/installation`. A complete recursive comparison with symlinks compared as links returned no differences. The earlier `backups/pre-finalization-20260928-080531` remains protected separately. Restore the final snapshot to the original canonical root, then run `--check` and a model/save/reopen test. The `.aag-original` Wine DLL backups also allow individual rollback of the touch fallback, but reverting that fallback reintroduces the known direct-touch crash.

## Plugin Golden recovery

Use the verified snapshot and ownership receipts described in [PLUGIN-GOLDEN-DELTA.md](PLUGIN-GOLDEN-DELTA.md). Close the relevant prefix, preserve its current state, restore the selected snapshot directly at its original root, restore its launcher/configuration, and repeat cold-launch/model/save/desktop tests. Individual plugin rollback moves only receipt-owned additions outside search paths after checking shared dependencies. Neither path deletes Base Golden or user-provided installation material.

## Future promoted candidates

The [update workflow](UPDATE.md#rollback-and-rejection) changes explicit desktop entries while retaining both roots at their tested locations. Its private transaction journal stores exact before/after text for atomic replacement and recovery. Restore the matching documentation state as well; preserve all old Golden tags and check model file-format compatibility separately.
