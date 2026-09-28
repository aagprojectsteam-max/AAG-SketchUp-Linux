# Base Golden to Plugin Golden

Base: `stable-sketchup-2026-ubuntu-final`, commit
`f06aae42b0177ce8ffb4604b61d018c39287c44d`.
Plugin release: `stable-sketchup-2026-ubuntu-plugins`; resolve its commit with
`git rev-parse stable-sketchup-2026-ubuntu-plugins^{commit}`.

## Added

- 1,425 reviewed, unchanged vendor code/assets files: Pipe Along Path 2.2,
  KBS Face Tool 1.0.0, SketchUcation 5.0.6 and LibFredo6 15.8e.
- Prefix-local `ClientSideGraphics=N` and the original scoped popup presentation
  helper, built locally. [Painting evidence](WINDOW-PAINTING.md) explains why.
- Launcher validation and private runtime entry helper; isolated candidates have
  separate unit/lock names and verified read-only protected mounts.
- Metadata-only [production manifest](../artifacts/production-plugin-manifest.json),
  audited migration tools, original tests and documentation.

## Preserved and excluded

Application, x64 MSVCP, UCRT, runtime/prefix touch-patched user32, hardware
OpenGL, MSAA 8, LogPixels 192 and HIGHDPIAWARE match the protected baseline.
Original installation material and the real Windows installation were inputs
only. No Windows account/license data was copied. Existing bundled extensions
were retained, including newer Dynamic Components 1.8.5.

JointPushPull, FredoCorner and V-Ray payloads stay outside production and all
plugin search paths. Their user deferrals remain independent. Online features
of bundled optional extensions remain deferred. An unclassified vendor-folder
PDF, user presets, caches and vaults were excluded.

## Ownership and dependency ledger

The four promoted plugin groups own only the paths and per-file hashes in their
private durable copy receipts. The public manifest records versions, file counts,
aggregate manifest digests, ABI/imports, tested functions and limits. No vendor
payload is published. Pipe/KBS require the SketchUp Ruby geometry API. LibFredo6
requires Ruby 3.2 and CEF; its selected x64 module was observed under the private
prefix's normal Temp extraction path. SketchUcation's local manager uses CEF;
its licensing module is included and audited but not needed by the tested local
manager. Included native candidates must not be confused with loaded modules.
JointPushPull and FredoCorner would additionally depend on LibFredo6 and
SketchUcation after legitimate activation.

The helper source SHA-256 is
`fd17421107e522d21d6adf84271feb4896db79d8e74e3b098c0ad167be93cfca`;
the tested local build is
`cd8c047ea63d949544830e584fbf598c8d9aa9bf2f02f5c2fe0cf69fa1e8526e`.
Compiler differences can change the build hash; rebuild the manifest and retest.

## Recovery

Protected pre-plugin snapshot: `BASE_GOLDEN_BEFORE_PLUGIN_MIGRATION-20260928-120534`.
Its 38,772 regular files were rehashed successfully. Original final and earlier
rollback snapshots remain separate and untouched.

Final plugin snapshot: `PLUGIN_GOLDEN-20260928-final/installation`, verified
against the closed installation: 40,254 regular files and 3,591 symlink targets.
The earlier plugin snapshot is retained too. Restore at the original canonical
path while closed; relocating a prefix has previously failed. Snapshot manifests
and exact private paths remain local. [Rollback](UNINSTALL-ROLLBACK.md) and
[individual plugin rollback](PLUGIN-MIGRATION.md#promotion-and-individual-rollback)
include the required checks. Promotion never deletes the old Golden.
