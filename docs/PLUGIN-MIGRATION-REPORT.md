# Plugin migration release report

## Executive summary

PLUGIN_MIGRATION_GOLDEN=YES for the tested local feature set, dated 2026-09-28.
Thirteen unique Windows/bundled extensions were inventoried. Four are compatible
in their tested modeling scope, two have a partial/local scope, six have optional
user actions deferred, and one bulk-migration feature is not tested. No extension
is classified incompatible. No user action is currently required.

## Windows source audit and safety

Windows was read-only input. Sources, loaders, shipped extensions, native modules
and user-data locations were inventoried independently; no registry, account,
activation, password, license token or Windows service state was imported.
[Inventory](WINDOWS-PLUGIN-INVENTORY.md) records provenance and duplicate versions;
[user data](PLUGIN-USER-DATA.md) records exclusions. Source hashes were checked
against validated candidate files before the exclusive production copies.

## Inventory, classification and native architecture

[PLUGINS.md](PLUGINS.md) is the complete per-extension matrix. Four promoted
plugin groups contribute 1,425 files. The complete production plugin tree has
1,833 files, 14 x64 PE modules and two inactive historical x86 modules. Inactive
Mac/old-ABI payloads were identified separately; no ARM64 module was selected.
The public [manifest](../artifacts/production-plugin-manifest.json) records
native hashes/imports and the [delta](PLUGIN-GOLDEN-DELTA.md) is the ownership and
dependency ledger. No plugin symlink depends on Windows or a temporary test root;
files were not made world-writable. Native extraction to the private Wine Temp
folder is normal vendor behavior, not dependence on a disposable test install.

## Isolated validation

A fresh candidate prefix followed a failed relocated-prefix experiment. The
real Windows source, production and backups were verified read-only inside its
runtime container. It has separate logs, prefix, unit and lock; home-directory
sharing means this is not a complete security sandbox. Base geometry/save/reopen
passed before plugin testing. The source launcher now supports these independent
units without a private hand-edited launcher.

## Compatible extensions

Pipe Along Path 2.2 created a real pipe (145 edges, 50 faces), with parameter UI
and Hebrew-path save/reopen. KBS 1.0.0 created a face and its center through actual
toolbar buttons, with save/reopen. A disconnected test fixture was corrected;
no vendor code changed. Existing Dynamic Components 1.8.5 resized a dynamic cube
to 20×30×40 inches; Sandbox 2.3.5 created a 14-face terrain. Both survived reopening.

## Partial extensions

SketchUcation 5.0.6 passed actual local-manager GUI disable/re-enable callbacks,
including restoration of the original loader hash after repeated dialog opens.
LibFredo6 15.8e passed native dependency loading and settings/defaults UI and
persistence. Optional store/licensed dependent operations are outside these PASS
scopes. Toolbar visibility alone is not functional evidence.

## Incompatible, not tested and user actions

Incompatible: none. Migrate Extensions 1.0.1 is preserved; its bulk import was not
used. JointPushPull, FredoCorner and V-Ray were individually deferred by the user;
load/license or legal UI observations remain separate from unperformed activation
and functional tests. Add Location, AI Assistant and AI Render online features
are also deferred. No agreement was accepted by the scripts and no licensing was
bypassed. These optional deferrals do not block this release.

## Production promotion and final regression

Production was closed; reviewed plugin copies and scoped painting support were
installed after verified Base backup. Combined tests passed: actual Line,
Rectangle, Push/Pull, selection/deletion, Orbit/Pan/Zoom, save/reopen and geometry
preservation; actual GNOME Apps and Dock launches, existing-window focus, a single
Dock identity, maximize/restore, sharp 192-DPI UI and pointer hit testing.
Classic hardware OpenGL, MSAA 8 and the exact guarded touch repair were preserved.
The [painting report](WINDOW-PAINTING.md) contains repetitions, frame statistics,
A/B results and the eight PASS gates.

Final clean production cold launches: 10.42, 10.23, 10.45 seconds to the saved
model. All three closed without a new dump or remaining prefix processes.
A roughly 24-minute combined modeling/dialog exercise had no late SketchUp crash.
An earlier instrumented candidate rapid-close crash remains documented, with an
unresolved root cause and subsequent clean candidate/production retests. The
baseline Xalia warning is also retained in that report. No repeating Ruby/plugin
load exception was found in accepted production runs.

## Performance impact

Matched candidate startup (same model/runtime, no QA loader): baseline mean
8.97 seconds; four added plugins mean 10.64 seconds, approximately +1.67 seconds.
Three samples each, sequential order and warm caches limit precision. These are
not a timing comparison against the original historical Base launch session.
Production startup mean was 10.37 seconds. Ninety synchronous redraws averaged
17.78 ms (p95 18.56) versus historical 18.77 ms (p95 19.54); scenes differed, so
this supports absence of a large regression, not a proven speed improvement.
Idle summed RSS was about 2.06 GiB versus 2.10 GiB historically; shared mappings
are counted more than once. A five-second idle CPU sample was about 4% of one
core versus roughly 3% historically. Large workloads remain untested.

## Base preservation and plugin backup

[The delta](PLUGIN-GOLDEN-DELTA.md) records independently verified Base and Plugin
snapshots. The historical Base tag still resolves to its original commit. The
plugin release has a new immutable tag; it does not redefine the Base release.

## Cleanup and desktop state

Temporary Ruby QA loaders were moved outside both plugin search paths. Test
models, videos, crash data and copy receipts remain private evidence. Deferred
payloads are held outside production. No additional irreversible deletion was
performed. Input Lock is restored to Unlocked/SAFE_NORMAL with zero grabbed
devices; mouse acceleration is default and the Hebrew input layout is restored.
The original session-manager state and Steam-client removal are preserved.
The required private GE-Proton/sniper directories remain independent of Steam.

## GitHub publication

Repository: [AAG-SketchUp-Linux](https://github.com/aagprojectsteam-max/AAG-SketchUp-Linux).
Release: `stable-sketchup-2026-ubuntu-plugins` (resolve the commit from the tag).
Only original support sources, documentation and sanitized metadata are published.
The complete staged tree passes the explicit publication allowlist, secrets,
private-path and binary checks. Remote commit/tag equality and clean worktree
are checked after pushing; the local publication receipt records those results.

## Limits and rollback

[The compatibility matrix](PLUGINS.md) gives tested feature boundaries. No new
reboot, full cloud workflow, licensed render, complex-pipe or large-project claim
is made. Follow [individual rollback](PLUGIN-MIGRATION.md#promotion-and-individual-rollback)
or restore the verified Base/Plugin snapshot at its original root. Keep receipts
and dependencies together; never copy Windows licensing state to recover a tool.

The [acceptance matrix](plugin-acceptance.json) covers every mandatory technical
migration and painting gate. Historical failures are retained in the narrative.
