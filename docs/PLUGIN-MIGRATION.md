# Controlled extension migration

Read [the inventory](WINDOWS-PLUGIN-INVENTORY.md) and [the matrix](PLUGINS.md)
before copying an extension. Supply your own legitimate extension packages and
licenses. This repository contains no third-party extension code or RBZ files.

## Protect the working installation

1. Save or close models with the user's permission. Verify that all processes
   belonging to the production prefix have exited; leave unrelated Wine apps alone.
2. Create a separate timestamped `BASE_GOLDEN_BEFORE_PLUGIN_MIGRATION` snapshot.
   Preserve the original Golden backup as well. Copy the installation, prefix,
   launchers and configuration; compare files and record hashes.
3. Create a candidate at a permanent separate path with its own prefix, logs,
   runtime copy, systemd unit and launcher lock. Do not change Apps or Dock yet.
4. Expose the Windows source, production root and backups read-only inside the
   candidate container. Verify the effective mounts with `statvfs`, not just an
   environment-variable string. A broad `/run/media` setting alone was
   insufficient: explicit Windows mount paths and a pre-launch guard were needed.
5. Remove inherited candidate drive mappings to production/raw devices and
   rebase candidate runtime links. Keep user folders inside the candidate.

A relocated prefix failed at modeler initialization with `double free or
corruption` and an invalid exception frame **before any new plugin was added**.
Its exact underlying cause is unresolved. The failed prefix was preserved. A
fresh prefix with the same application/runtime and documented settings passed
modeling and save/reopen after the user personally accepted Trimble's terms.
Do not attribute that relocation failure to an extension, or copy the old
prefix blindly into future major releases.

## Audit and copy

```sh
python3 scripts/audit-plugins.py --source "$WINDOWS_PLUGIN_ROOT" \
  --output "$PRIVATE_EVIDENCE/windows-plugin-inventory.json"
python3 scripts/migrate-plugin.py --source "$WINDOWS_PLUGIN_ROOT" \
  --destination "$CANDIDATE_PLUGIN_ROOT" --plugin PipeAlongPath \
  --current-root "$SKETCHUP_ROOT" --dry-run
```

Review the planned file list. For the actual candidate copy, replace `--dry-run`
with `--receipt "$PRIVATE_EVIDENCE/pipe-copy.json"`. Existing targets are refused.
The script rejects source/destination overlap, real Windows destinations,
symlinks, likely license-state files and a running destination prefix. The
receipt is local evidence; it can contain private paths. It is durably updated
after every copied file. An interrupted copy retains its files and records
`PARTIAL_COPY_REQUIRES_REVIEW`; review that receipt before recovery. A manually
written PASS JSON is a review record, not independent proof of successful tests.

Test Ruby-only extensions first, one at a time. Restart after installation.
Check actual geometry, undo, UI commands, pointer accuracy, save/reopen, startup
errors, late crashes and shutdown. For native extensions, verify architecture,
Ruby ABI, imports and selected module before execution. Keep inactive vendor
platform/ABI payloads distinct from accidentally loaded incompatible modules.

Test HtmlDialog callbacks, not just HTML rendering. SketchUcation's manager was
checked by disabling and re-enabling the candidate's Pipe Along Path loader and
verifying that its original hash was restored. Do not relax extension loading
security or replace signature files.

Online stores, renderer licenses and legal agreements require legitimate user
action. An optional blocked extension stays outside production while other
extensions continue through their gates. Do not copy Windows activation state,
change the clock, bypass checks or label a toolbar-only result as PASS.

## Promotion and individual rollback

Only a reviewed local PASS record can authorize `migrate-plugin.py` to copy into
production. It must contain the exact proposed `files` list, the plugin ID, an
independent `rollback_path` containing its snapshot manifest, and PASS gates:
`LOAD`, `FUNCTION`, `GUI`, `SAVE_REOPEN`, `RESTART`, `NO_CRASH`, `ARCHITECTURE`,
`ROLLBACK`. Keep that evidence private. The gate means the documented tested
scope passed; optional untested features must remain explicit in the matrix.

Close production, verify the backup, dry-run with `--production-evidence`, then
copy with an explicit receipt. No existing files are overwritten. Validate the
combined production set again, including Apps/Dock, three cold launches and the
original graphics/DPI/touch requirements. Create a new plugin Golden backup and
immutable plugin tag only after those tests pass.

For individual rollback, close the prefix and move only the receipt's added
files to a dated private quarantine outside every plugin search path. Check
shared dependencies first: JointPushPull and FredoCorner use LibFredo6 and
SketchUcation. Preserve those libraries while a retained dependent uses them.
Restore any separately backed-up settings, then repeat a cold launch and model
save/reopen. For complete rollback, follow [UNINSTALL-ROLLBACK.md](UNINSTALL-ROLLBACK.md)
and restore the independent pre-plugin snapshot. Never delete the previous
Golden as part of promotion.

## Update behavior and limits

LibFredo6 displayed a periodic update-check prompt. The test selected **Later**;
no extension update was installed. SketchUcation store/update features require
separate review. Future extension updates must repeat native ABI and functional
checks. Vendor files remain unmodified; fixes belong in documented scoped
configuration or the candidate, not in opaque patched proprietary code.

Pressure-vessel mount configuration follows
[Valve's directory-sharing documentation](https://github.com/ValveSoftware/steam-runtime/blob/master/doc/steamlinuxruntime-known-issues.md#sharing-directories-with-the-container).

## Window painting acceptance

[Window painting regression](WINDOW-PAINTING.md) adds mandatory repeated focus,
context-menu, menu-bar, toolbar-popup and plugin-dialog painting gates. These
apply to candidate testing, production promotion and every future update. A
window repainting once is not sufficient evidence of a fix.
