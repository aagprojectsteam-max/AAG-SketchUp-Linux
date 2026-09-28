# Cleanup and storage ledger

Both exact deletion lists were approved. Before deleting each major path, the final launcher, prefix, runtime, rollback, original media and required scripts were checked for references. Twenty-four rollback font links were first rebased to the rollback runtime. All 17 authorized items were removed. No extra irreversible deletion scope was added.

## Deleted items

```text
DELETED=$WINEAPPS/SketchUp-Wine11
REASON=superseded SketchUp experiment; original material and text evidence preserved separately
REFERENCED_BY_FINAL_INSTALLATION=NO

DELETED=$WINEAPPS/SketchUp-Wine2026
REASON=superseded SketchUp experiment; original material and text evidence preserved separately
REFERENCED_BY_FINAL_INSTALLATION=NO

DELETED=$WINEAPPS/SketchUp-Wine11-test-old-20260923-221113
REASON=superseded SketchUp experiment; original material and text evidence preserved separately
REFERENCED_BY_FINAL_INSTALLATION=NO

DELETED=$WINEAPPS/SketchUp
REASON=superseded SketchUp experiment; original material and text evidence preserved separately
REFERENCED_BY_FINAL_INSTALLATION=NO

DELETED=$WINEAPPS/SketchUp-Proton
REASON=superseded SketchUp experiment; original material and text evidence preserved separately
REFERENCED_BY_FINAL_INSTALLATION=NO

DELETED=$WINEAPPS/sketchup-linux
REASON=superseded SketchUp experiment; original material and text evidence preserved separately
REFERENCED_BY_FINAL_INSTALLATION=NO

DELETED=$WINEAPPS/sketchup-2026-alt
REASON=superseded SketchUp experiment; original material and text evidence preserved separately
REFERENCED_BY_FINAL_INSTALLATION=NO

DELETED=$STEAM_DATA/steamapps/common/SteamLinuxRuntime_4
REASON=obsolete SketchUp-only Steam experiment; required runtimes relocated and verified
REFERENCED_BY_FINAL_INSTALLATION=NO

DELETED=$STEAM_DATA/steamapps/common/SteamLinuxRuntime_sniper
REASON=obsolete SketchUp-only Steam experiment; required runtimes relocated and verified
REFERENCED_BY_FINAL_INSTALLATION=NO

DELETED=$STEAM_DATA/steamapps/common/AAG-SketchUp-2026
REASON=obsolete SketchUp-only Steam experiment; required runtimes relocated and verified
REFERENCED_BY_FINAL_INSTALLATION=NO

DELETED=$STEAM_DATA/steamapps/common/AAG-SketchUp-2026-26.2-backup-20260925-073542
REASON=obsolete SketchUp-only Steam experiment; required runtimes relocated and verified
REFERENCED_BY_FINAL_INSTALLATION=NO

DELETED=$STEAM_DATA/steamapps/compatdata/<historical-app-id>
REASON=obsolete SketchUp-only Steam experiment; required runtimes relocated and verified
REFERENCED_BY_FINAL_INSTALLATION=NO

DELETED=$STEAM_DATA/steamapps/compatdata/0
REASON=obsolete SketchUp-only Steam experiment; required runtimes relocated and verified
REFERENCED_BY_FINAL_INSTALLATION=NO

DELETED=$STEAM_DATA/steamapps/compatdata-backups/<historical-app-id>-mixed-ge10-ge11-20260925-075252
REASON=obsolete SketchUp-only Steam experiment; required runtimes relocated and verified
REFERENCED_BY_FINAL_INSTALLATION=NO

DELETED=$STEAM_DATA/steamapps/shadercache/<historical-app-id>
REASON=obsolete SketchUp-only Steam experiment; required runtimes relocated and verified
REFERENCED_BY_FINAL_INSTALLATION=NO

DELETED=$STEAM_DATA/compatibilitytools.d/GE-Proton10-25
REASON=obsolete SketchUp-only Steam experiment; required runtimes relocated and verified
REFERENCED_BY_FINAL_INSTALLATION=NO

DELETED=$STEAM_DATA/compatibilitytools.d/GE-Proton11-7-x86_64
REASON=obsolete SketchUp-only Steam experiment; required runtimes relocated and verified
REFERENCED_BY_FINAL_INSTALLATION=NO

```

Removed allocated size: **60,566,663,168 bytes (56.41 GiB)**. This is the sum of pre-delete allocated sizes, not a claim about distinct physical extents on a reflink filesystem.

## Other completed cleanup

Steam Flatpak was uninstalled. Required GE-Proton10-25 and sniper live under the canonical root and remain installed. Obsolete masks/background blocks, Steam URI launch triggers and obsolete Wine associations were removed or archived. YAWMS is enabled, with autoclose=true, restore-previous=false, autorestore=false and stash-and-restore=true. Its active session contains no Steam entry. Three additional stale window mappings were backed up and removed without replacing unrelated mappings.

Temporary CEF ports 9222/9224/9226 are closed. Failed input shims and Ruby measurement plugins are archived outside the production configuration. Pre-finalization dumps remain in private evidence; no new dump appeared in the final three launches. All three closes left zero processes for the canonical prefix. Other Wine applications continue independently.

## Retained deliberately

| Material | Reason |
| --- | --- |
| Canonical app, prefix, GE-Proton and sniper | Required production installation |
| Original application/content and three installer files | User-owned source material; final hashes match preserved originals |
| `backups/final-golden-20260928/installation` | Complete final rollback; verified identical while closed |
| `backups/pre-finalization-20260928-080531` | Explicitly protected earlier known-good state, user model and historical recovery evidence |
| Older small configuration snapshots | Recovery/history; retained within the private backup area |
| Former workspace app/prefix copies | Moved into the historical backup area, no production launcher references |
| Private Steam account/client-data remnants | Outside the exact authorized deletion lists; no installed/running Steam client and no runtime dependency |
| Project code, documentation and private diagnostic evidence | Reproduction, maintenance and technical history |

Retained historical copies are backups, not alternate launchable production installations. The earlier known-good backup was not deleted to meet an arbitrary one-backup target. No unrelated Wine application, real Windows installation, user project or source media was changed.

## Storage after cleanup

Allocated sizes from `du -s -B1`; shared extents may be counted more than once.

| Component | Bytes | GiB |
| --- | ---: | ---: |
| Application | 1,034,125,312 | 0.963 |
| Prefix | 1,158,860,800 | 1.079 |
| Required runtime | 3,116,920,832 | 2.903 |
| Final rollback | 5,312,245,760 | 4.947 |
| Protected earlier rollback/history | 15,253,184,512 | 14.206 |
| Documentation | 135,168 | 0.000 |
| Original source/media | 3,500,187,648 | 3.260 |

DISK_CLEANUP_AUDIT=PASS
