# Golden history

Tags are immutable. Documentation/tooling commits after a tag do not change the
application state that tag records.

| State | Date | SketchUp | Tag | Release commit | Rollback |
|---|---|---|---|---|---|
| Base Golden | 2026-09-28 | 26.1.252 x64 | `stable-sketchup-2026-ubuntu-final` | `f06aae42b0177ce8ffb4604b61d018c39287c44d` | Original final Golden snapshot and independent pre-plugin snapshot |
| Plugin Golden | 2026-09-28 | 26.1.252 x64 | `stable-sketchup-2026-ubuntu-plugins` | `785b2e1ee921f055273f99221e34f6a084e22d46` | Verified `PLUGIN_GOLDEN-20260928-final` snapshot; Base backup retained |

Both use GE-Proton10-25, private sniper 3.0.20260805.254768, Wine 10.0 Staging,
Classic hardware OpenGL on Intel Arc/Mesa 26.0.8, MSAA 8, 192 DPI/HIGHDPIAWARE,
the exact guarded Wine touch alias, correct x64 MSVCP, native UCRT and complete
ProgramData. The separate content version 26.2 is an explicitly tested exception.
The Plugin state adds four reviewed extension groups and scoped painting fixes.
See [Base configuration](GOLDEN-STATE.md), [plugin delta](PLUGIN-GOLDEN-DELTA.md)
and [plugin matrix](PLUGINS.md) for evidence and limits.

## Update framework

The later framework commit adds preparation, audit, validation, reversible
launcher promotion and recovery tooling. Its current-Golden self-test used a
new fresh-prefix candidate and then rejected it as a test artifact. Production
remained byte-for-byte unchanged. No new application tag or fake update was made.
[Framework report](UPDATE-FRAMEWORK-REPORT.md) documents the checks.

## Add a future Golden

Add a row only after real base/plugin and post-promotion acceptance. Record date,
actual application/content/runtime versions, graphics/DPI, required and removed
fixes, plugin scope, exact commit/new tag, active launcher target and verified
rollback reference. Keep private paths in local records. Add a sanitized
[per-version report](updates/TEMPLATE.md); do not overwrite prior evidence.

## Networking support maintenance

The 2026-09-29 maintenance change adds secure host-trust integration and verified core sign-in/persistence to the same app/runtime. It preserves both historical tags and independent backups. It does not create an application-upgrade tag. See [networking results](NETWORKING.md) and the [gate record](network-acceptance.json), including optional service limitations.

## 2026-09-29 — Hebrew input maintenance

Added a conditional shared-Xwayland map repair and mandatory bilingual update gates. Networking and original binary/content baselines remain preserved. No historical Base/Plugin tag is moved. See [the input investigation](HEBREW-INPUT.md) and [current matrix](hebrew-input-acceptance.json).
