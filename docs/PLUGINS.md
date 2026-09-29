# Extension compatibility matrix

**Plugin Golden: production regression passed on 2026-09-28.**
The Base Golden tag and independent backups remain unchanged. See the
[release report](PLUGIN-MIGRATION-REPORT.md) and [delta](PLUGIN-GOLDEN-DELTA.md).

The table below is the original 2026-09-28 Plugin Golden inventory.
Current bundled-version changes are recorded after it.

| Extension | Validated result | Evidence / limit | Production decision |
|---|---|---|---|
| Pipe Along Path 2.2 | Functional PASS | Menu/input dialog; 145 edges/50 faces; Hebrew-path save/reopen; restart | Installed; production functional regression PASS |
| KBS Face Tool 1.0.0 | Functional PASS | Make face and center point; save/reopen; restart | Installed; production functional regression PASS |
| SketchUcation 5.0.6 | Local manager PASS | HTML disable/re-enable callback and hash preservation; licensing module loads | Installed; local manager PASS; online store deferred |
| LibFredo6 15.8e | Library/settings PASS | Ruby 3.2 native module selected; defaults UI opened/saved; restart | Installed; dependency/settings scope PASS |
| JointPushPull 4.9a | USER_ACTION_DEFERRED | Load and licensing UI PASS; activation deferred by user; functional test NOT_TESTED | Hold outside production; does not block plugin Golden |
| FredoCorner 2.7a | USER_ACTION_DEFERRED | Load and licensing UI PASS; activation deferred by user; functional test NOT_TESTED | Hold outside production; does not block plugin Golden |
| V-Ray 7.30.00 | USER_ACTION_DEFERRED | Legal agreement UI PASS; terms not accepted; activation and render test not performed by user choice | Hold outside production; does not block plugin Golden |
| Add Location 1.8.2 | Existing bundled extension | Sign-in UI reached; account functionality USER_ACTION_DEFERRED | Preserve existing version |
| AI Assistant 1.0.3 | Existing bundled extension | Sign-in UI reached; account functionality USER_ACTION_DEFERRED | Preserve existing version |
| AI Render 1.2026.02.26 | USER_ACTION_DEFERRED | Native bridge loaded; online check unavailable; base Golden has AI Render disabled | Preserve base disabled state |
| Dynamic Components | Existing Linux 1.8.5 | Windows has older 1.8.3; real dynamic cube resized to 20×30×40 inches and survived save/reopen | Preserve newer version |
| Migrate Extensions 1.0.1 | Existing bundled extension | Same loader; bulk Windows migration not used | Preserve existing version |
| Sandbox Tools 2.3.5 | Existing bundled extension | From Contours produced 14 terrain faces / 26 edges / height 60 inches; save/reopen PASS | Preserve existing version |

See [inventory](WINDOWS-PLUGIN-INVENTORY.md), [migration and rollback](PLUGIN-MIGRATION.md)
and [user-data policy](PLUGIN-USER-DATA.md). Raw inventories, vendor payloads,
models, screenshots of account dialogs and crash data stay private.

## JointPushPull user decision

```text
JointPushPull:
LOAD=PASS
LICENSING_UI=PASS
ACTIVATION=NOT_PERFORMED_BY_USER_CHOICE
FUNCTIONAL_TEST=NOT_TESTED
RESULT=USER_ACTION_DEFERRED
```

This is a user deferral, not an incompatibility or failure. No activation data
was copied or bypassed. This decision applies only to JointPushPull. Its deferred
status does not block plugin Golden if the remaining required gates pass.

## FredoCorner user decision

```text
FredoCorner:
LOAD=PASS
LICENSING_UI=PASS
ACTIVATION=NOT_PERFORMED_BY_USER_CHOICE
FUNCTIONAL_TEST=NOT_TESTED
RESULT=USER_ACTION_DEFERRED
```

The user deferred activation independently of JointPushPull. This is not a failure
or an incompatibility. No license state was changed. Neither deferred extension
blocks plugin Golden when all remaining mandatory gates pass. Accessible Fredo
dialogs may still be used to test window painting without activating a license.

## V-Ray / Chaos user decision

```text
V-Ray / Chaos:
DISCOVERED_IN_WINDOWS_PLUGIN_INVENTORY=YES
MIGRATION_ATTEMPTED=YES
LEGAL_AGREEMENT_UI=PASS
LEGAL_AGREEMENT_ACCEPTED=NO
ACTIVATION=NOT_PERFORMED_BY_USER_CHOICE
FUNCTIONAL_TEST=NOT_TESTED
RESULT=USER_ACTION_DEFERRED
```

This is a user deferral, not a failure or an incompatibility. The agreement was
not accepted; no activation or render test was performed. No additional Chaos
services were installed. Further V-Ray engineering is deferred. JointPushPull,
FredoCorner and V-Ray do not block plugin Golden when the remaining required
gates pass. Additional optional account/legal gates are deferred by default;
only core requirements or explicitly requested plugin validation need user action.

## Bundled versions detected during networking maintenance

The protected Plugin Golden backup still contains Add Location 1.8.2 and AI
Assistant 1.0.3. The current prefix has Add Location **1.8.6** and AI Assistant
**1.0.5**. Filesystem change timestamps place these changes near the beginning
of the networking work, before the Hebrew-input investigation. The exact
installation mechanism was not established; this is not attributed to the
keyboard helper. These version differences were found during the final hash
audit and are not hidden by a claim that every plugin file is unchanged.

All 294 checked source/native/web-code files belonging to the migrated
LibFredo6, SketchUcation, Pipe Along Path and KBS Face Tool packages still match
the protected Plugin Golden. The current Add Location search suggestions were
verified, with its map WebGL limitation retained. AI Assistant generation was
not tested. Neither changed package nor any vendor binary is published.

Keep the historical backup for rollback. Re-inventory bundled extensions when
network access or an application update changes their versions; the framework
must review that drift separately from migrated third-party plugin code.
