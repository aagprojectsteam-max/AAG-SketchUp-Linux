# Safe SketchUp updates

This is the authoritative update procedure. **An audit or successful preparation
is not GUI acceptance.** Keep the active Golden, its independent backup and each
candidate separate. No new SketchUp version was promoted while building this
framework. Unknown releases may need new engineering.

## Locate the current installation and evidence

Read [current-golden-baseline.json](../artifacts/current-golden-baseline.json),
[GOLDEN-HISTORY.md](GOLDEN-HISTORY.md), [PLUGINS.md](PLUGINS.md),
[ROOT-CAUSE.md](ROOT-CAUSE.md) and [WINDOW-PAINTING.md](WINDOW-PAINTING.md).
The current Apps entry is normally
`$XDG_DATA_HOME/applications/aag-sketchup-2026.desktop`, with XDG_DATA_HOME
falling back to `$HOME/.local/share`. Read its `Exec=` value to locate the active
root; do not assume a path from an old chat. There may also be a Desktop copy.
The root contains `app`, `compatdata`, `runtime`, `bin`, `config` and `logs`.

Set explicit paths below. Variables are examples to fill in, not default targets.
The rollback directory must contain `installation/` and a full `manifest.json`
with relative `files` entries (`sha256`, `bytes`) and `symlinks` targets. Close
that installation before creating/verifying the snapshot. The original Base
and Plugin backups must both remain available.

```sh
CURRENT_ROOT='<active installation root>'
CANDIDATE_ROOT='<new permanent candidate path>'
APP_SOURCE='<complete legitimate new application directory>'
CONTENT_SOURCE='<matching ProgramData SketchUp content directory>'
RUNTIME_SOURCE='<directory containing one Proton and one sniper runtime>'
ROLLBACK_ROOT='<verified independent current Golden snapshot directory>'
BACKUPS_ROOT='<directory containing all protected Golden snapshots>'
PRIVATE_EVIDENCE='<new private update evidence directory>'
```

Supply your own legitimate app/content/runtime files. This is not an installer
extractor or downloader. Never obtain arbitrary DLLs from download sites. Record
installer/package versions, official origin, package hashes and extraction method
in private evidence. Microsoft runtime replacements need legitimate Microsoft
package provenance and an x64 PE/hash audit. Windows and installation media are
inputs only; the tool never modifies them.

## Audit and dry-run

Python 3.9+ is required. Launching also needs the existing systemd user session,
wmctrl, Xwayland and the supplied runtime. Building the optional original popup
helper needs the compiler/X11/XCB headers listed in [INSTALL.md](INSTALL.md).
No command here installs host packages or changes system graphics/input settings.

```sh
python3 -B scripts/prepare-update.py audit \
  --current-root "$CURRENT_ROOT" --candidate-root "$CANDIDATE_ROOT" \
  --app-source "$APP_SOURCE" --content-source "$CONTENT_SOURCE" \
  --content-version '<actual separate content version>' \
  --runtime-source "$RUNTIME_SOURCE" --rollback-root "$ROLLBACK_ROOT" \
  --protect-root "$BACKUPS_ROOT" --plugin-policy revalidate \
  --source-note '<legitimate provenance and package hashes>' \
  --dry-run --report "$PRIVATE_EVIDENCE/audit.json"
```

Without `--report`, audit writes nothing. With it, only the explicitly selected
new private report is created outside protected inputs. `create --dry-run` is
also an audit. Other mutating commands reject `--dry-run` instead of ignoring it.
Reports contain private paths and filenames: **do not publish them unchanged**.

The audit reads actual PE architecture, bounded version resources, hashes, imports
and exports. SketchUp's fixed numeric version can be `26.0.0.0` while bounded
StringFileInfo says `26.1.252`; conflicting/missing string builds require review.
It compares full application/content/runtime manifests, records native critical
file metadata on both sides and flags Qt, CEF, Ruby, VC/UCRT and graphics changes.
Missing content categories or StyleTemplate, wrong/unknown app native architecture,
insufficient disk, an incomplete runtime or a bad backup prevents creation.
Inactive mixed-architecture app payloads need a reviewed exception in future
engineering; the tool does not guess that they are safe.

Expected content includes Styles, Materials, Components, Environments,
HatchPatterns, Workspaces and Tutorials. New releases may need additional resources.
The current 26.1.252/26.2-content combination is a tested exception; a mismatch
remains visible and needs a specific `CONTENT_VERSION_REVIEW` gate.

Update classifications are SAME_BUILD_REINSTALL, PATCH_UPDATE, MINOR_UPDATE,
MAJOR_UPDATE, RUNTIME_ONLY_CHANGE, PLUGIN_ONLY_CHANGE and UNKNOWN. Hash/framework
changes matter even when version strings do not change. Known matching files use
a metadata fast path, while every guard and mandatory GUI gate still applies.
Unknown builds report `REQUIRES_AUDIT`; they do not inherit all old fixes.

## Prepare and initialize a fresh candidate

Repeat the audited command with `create` instead of `audit` and omit `--dry-run`.
Choose a new report filename if using `--report`. The destination must not exist.
The tool copies and verifies the app, matching content and private runtime. It
creates a fresh `compatdata` directory, independent logs and a candidate manifest.
It does not clone account state, plugins, caches or the current prefix.

Then:

```sh
python3 -B scripts/prepare-update.py initialize --candidate-root "$CANDIDATE_ROOT"
python3 -B scripts/prepare-update.py status --candidate-root "$CANDIDATE_ROOT"
```

Initialization runs only `cmd /c exit 0` to create the fresh prefix, copies content
into the detected year-specific ProgramData location and redirects generated
host-user-folder links into empty candidate-local folders. It removes only new
candidate drive links beyond c:/z:. The current prefix and Windows are not edited.
A failed partial initialization is retained in PREFLIGHT_FAILED; inspect it,
reject the candidate and use a new destination after fixing the cause. Do not
merge a partially initialized prefix blindly or relocate a tested one.

The candidate manifest records sources, runtime provenance, prefix strategy,
fix decisions, differences, graphics/DPI decisions, plugin plan, history and test
status. The candidate's `SketchUp-TEST.desktop` stays inside its root; it is not
installed in Apps or pinned. Its launcher uses a unique unit and lock, scoped by
candidate ID. During execution, pressure-vessel exposes production, source paths,
explicit protected backups and detected Windows volumes read-only. It checks
actual mount flags before executing Proton and records the result. This protects
those paths; broadly shared home/session services mean it is not a complete
security sandbox. Include every additional protected backup via `--protect-root`.

## Reevaluate compatibility fixes

[compatibility-rules.json](../config/compatibility-rules.json) classifies rules as
ALWAYS_REQUIRED, VERSION_SPECIFIC, RUNTIME_SPECIFIC, LEGACY_ONLY or UNKNOWN, and
separates narrowly eligible automatic work from reviewed engineering.

| Fix | Decision |
|---|---|
| MSVCP140 | Keep a supplied correct x64 DLL. ARM64/x86 blocks preparation; acquire/audit legitimate x64 input, then repeat audit. No blanket replacement. |
| UCRT | First test legitimate supplied/default runtime. Only a proven dependency/failure justifies the native override. Ruby/VC/Wine changes require review. |
| Touch export | Exact stock hash + known GE runtime + missing export permits the guarded patch. Pass `--apply-known-touch` explicitly to initialize. Exact patched hash is a no-op. Unknown absent export requires engineering. A future export means no legacy patch; its behavior still needs testing. |
| DPI/CEF/font | Re-test menus, tray, toolbar, Welcome, HTML, native viewport size and hit testing. Prefer simpler settings if proven correct. |
| Classic/MSAA8 | Test the known hardware path where supported; inspect candidate-supported engines. Never silently replace hardware rendering with software. |
| Painting | Re-test focus and first paint using actual compositor recordings. Old window-style/X11 assumptions may no longer hold. |
| Content | Use version-matched complete content. Document/test any mixed-version exception; do not universally reuse the old restoration. |

Initially keep the known runtime. A justified runtime change gets a separate
candidate; do not simultaneously vary SketchUp, Proton, sniper, Mesa, DPI and
renderer. A native touch implementation may remove the old alias; test mouse,
touchpad, pointer accuracy and safely reproducible direct-touch behavior again.

For an **exact unchanged known-build reinstall only**, `configure-known` provides
an explicit reviewed recipe for the existing UCRT/DPI/Classic/CEF/font/painting
configuration. It refuses changed app/content/runtime metadata. Its private
`--evidence` JSON must contain `candidate_id`, `reviewer`, an `evidence` list,
`runtime_provenance`, and these reasoned decisions, each `YES`:
`UCRT_REQUIRED`, `DPI_REQUIRED`, `CLASSIC_MSAA8_REQUIRED`, `PAINTING_REQUIRED`,
`CEF_GPU_WORKAROUND_REQUIRED`, `FONT_FILTER_REQUIRED`.

```sh
python3 -B scripts/prepare-update.py configure-known \
  --candidate-root "$CANDIDATE_ROOT" --ucrt-source '<legitimate tested x64 UCRT>' \
  --evidence "$PRIVATE_EVIDENCE/compatibility-review.json"
```

This optional recipe is not a shortcut for a future changed build. For narrower
or new fixes, edit only the candidate after evidence review; record exact changes
in its manifest and `docs/updates/<version>.md`. Re-audit architecture, dependencies
and hashes. Never patch a close-enough Wine binary or proprietary application.

## Base and plugin regression

```sh
python3 -B scripts/prepare-update.py template --candidate-root "$CANDIDATE_ROOT" \
  > "$PRIVATE_EVIDENCE/regression.json"
python3 "$CANDIDATE_ROOT/bin/launch-sketchup.py"
```

Template fields begin NOT_TESTED. PASS values are reviewer attestations backed
by local evidence, not independent machine proof. No script accepts legal terms,
logs into accounts or copies activation state. Core licensing/terms require the
user at the real visible window. Optional plugins may be USER_ACTION_DEFERRED;
handle decisions independently and preserve the existing matrix.

Before migrating plugins, complete all base gates: actual Line/Rectangle/PushPull,
selection/deletion, Orbit/Pan/Zoom, save-as/reopen and geometry, sharp UI/DPI,
pointer accuracy, maximize/restore, hardware graphics/AA/native viewport, input,
painting/focus, three cold launches, bounded late-crash observation and clean
shutdown. The original [Ruby fixture](../tests/update-model.rb) can generate a
safe model in a fresh empty document. It does not replace real GUI tool tests.
Save only new private test files. Use copies of previous test models to inspect
new-format saves; record backward readability as YES/NO/UNKNOWN. Application
rollback does not make a changed file format backward compatible.

Record approximately comparable startup, redraw, idle memory and CPU. Use the
same model/runtime/cache conditions where possible; distinguish noise from a
meaningful regression. Qt/CEF/renderer/DPI changes require controlled visual
comparisons. Actual compositor output matters; XGetImage alone misses first-paint
flashes. Never mark an unfired menu click or interrupted workspace run PASS.

```sh
python3 -B scripts/prepare-update.py validate --phase base \
  --candidate-root "$CANDIDATE_ROOT" --evidence "$PRIVATE_EVIDENCE/regression.json"
```

Only after BASE_PASS, migrate reviewed code using [PLUGIN-MIGRATION.md](PLUGIN-MIGRATION.md).
Do not copy the whole old Plugins directory. Test every retained plugin's basic
function. Ruby changes require native ABI testing; CEF/Qt changes require HTML,
callbacks and dialogs; VC/UCRT changes require native dependency testing; graphics
changes require renderer tests. Record `name`, `result`, `installed`, `evidence`
for each plugin in the regression JSON. Allowed outcomes are PASS, PARTIAL, FAIL,
NOT_TESTED, UPDATE_REQUIRED and USER_ACTION_DEFERRED. Only PASS/PARTIAL payloads
can remain installed. A real regression requires informed user review before
replacing their plugin-enabled production; optional deferrals alone do not block.

```sh
python3 -B scripts/prepare-update.py validate --phase plugins \
  --candidate-root "$CANDIDATE_ROOT" --evidence "$PRIVATE_EVIDENCE/regression.json"
python3 -B scripts/prepare-update.py validate --phase ready \
  --candidate-root "$CANDIDATE_ROOT"
```

READY_FOR_PROMOTION requires a closed candidate, accepted base/plugin records,
reverified rollback and a fingerprint of its app/content/runtime/config/bin/prefix.
Later changes invalidate promotion. Prepare the correct icon in `config/icons/`
and any final candidate launcher adjustments **before** this fingerprint. To
extract the candidate's own icon without touching desktop integration, use
`wrestool -x -t 14 -n IDR_MAINFRAME -o <candidate.ico> <candidate SketchUp.exe>`,
inspect frames with `icotool -l <candidate.ico>`, then extract the appropriate
large PNG frame with `icotool -x --index=<reviewed index> -o <candidate PNG>
<candidate.ico>`. Store the PNG as `config/icons/sketchup.png` and inspect it.
Resource names/frame indexes may change. Do not run the legacy
`install-launcher.py` during candidate preparation: it installs production Apps
entries. Do not retarget the canonical desktop entry during candidate testing.

## Explicit reversible promotion

BUILD, VALIDATE and PROMOTE are separate commands. No audit or test triggers a
production update. Promotion keeps both roots at their original paths and changes
only explicitly listed desktop entries. Each entry replacement is atomic; multiple
entries use a durable journal and automatic error rollback. This is a recoverable
transaction, not a single filesystem-wide atomic commit.

Before promotion, prepare and review consistent canonical metadata: README tested
version, current Golden baseline, Golden history, plugin/test matrix and update
report, with a **new unused tag name**. The private metadata JSON contains:

```json
{
  "candidate_id": "<from candidate manifest>",
  "version": "<candidate build>",
  "repository": "<local repository path>",
  "rollback_root": "<verified snapshot path>",
  "new_tag": "stable-sketchup-<new-version>-ubuntu",
  "update_report": "docs/updates/<new-version>.md",
  "startup_wm_class": "<actually observed window class>",
  "backward_file_warning_reviewed": true,
  "plugin_changes_reviewed_by_user": true,
  "reviewed_files": {
    "README.md": "<sha256>",
    "artifacts/current-golden-baseline.json": "<sha256>",
    "docs/GOLDEN-HISTORY.md": "<sha256>",
    "docs/PLUGINS.md": "<sha256>",
    "docs/TEST-MATRIX.md": "<sha256>",
    "docs/updates/<new-version>.md": "<sha256>"
  }
}
```

The review flags must reflect an actual review/authorization, not defaults filled
by a script. Future task authorization may already cover understood routine
promotion; new plugin loss or unreadable older model formats require explicit
user understanding. Stage/review documentation, but publish/tag only after the
post-promotion gates pass. The tool verifies the listed hashes and unused tag;
it does not infer the meaning of prose or publish Git automatically.

```sh
python3 -B scripts/prepare-update.py promote --candidate-root "$CANDIDATE_ROOT" \
  --desktop-entry '<canonical Apps desktop entry>' \
  --desktop-entry '<Desktop copy, if present>' \
  --transaction "$PRIVATE_EVIDENCE/promotion-transaction" \
  --metadata "$PRIVATE_EVIDENCE/promotion-metadata.json"
```

It verifies the accepted candidate fingerprint, old launcher target, independent
rollback, candidate icon and reviewed actual window class, then records AWAITING_POST_PROMOTION_GUI. Close both
installations before this step. Retest Apps, Dock, existing-window focus, icon and
window matching, no duplicate icon, and combined modeling/save/plugin behavior.
Record real post-promotion gates and evidence, then:

```sh
python3 -B scripts/prepare-update.py finish --candidate-root "$CANDIDATE_ROOT" \
  --evidence "$PRIVATE_EVIDENCE/regression.json"
```

If an ordinary failure occurs, launcher writes are reversed. A power loss may
leave a PREPARED journal with a mix of original and new entries: keep both roots,
compare each entry with the journal, restore exact `before` text atomically, and
record recovery before retrying. Do not overwrite an entry changed independently
by the user. Git publication and filesystem launchers cannot form one atomic
transaction; the review journal, deferred tagging and documented recovery keep
metadata consistent.

## Rollback and rejection

```sh
python3 -B scripts/prepare-update.py rollback --candidate-root "$CANDIDATE_ROOT"
```

Rollback checks current launcher text before restoring the recorded entries;
both prefixes/roots remain intact. Re-test the restored Apps/Dock and a copied
model. Revert pending canonical metadata, or make a new rollback documentation
commit if already published. Never move either historical Golden tag.

For a candidate that never promoted:

```sh
python3 -B scripts/prepare-update.py reject --candidate-root "$CANDIDATE_ROOT" \
  --reason '<failure stage, cause/evidence, or self-test disposition>'
python3 -B scripts/prepare-update.py cleanup-plan --candidate-root "$CANDIDATE_ROOT" --dry-run
```

Cleanup only proposes the exact rejected path and evidence to preserve. It never
deletes a candidate, production, source or backup. Actual deletion needs applicable
explicit authorization and a final reference check against launchers, roots,
runtimes, rollback and original material. Keep previous Goldens until practical
use establishes stability and cleanup is explicitly appropriate; no automatic timer.

## Publish a real release

Update [Golden history](GOLDEN-HISTORY.md), baseline, README, matrix and per-version
report consistently. Record causes, evidence, fix scope/version dependency,
rollback and meaningful failed approaches. Retain raw models/videos/dumps/logs
privately. Do not repeat indiscriminate DLL accumulation, software-render defaults,
Steam installation, renderer changes for content crashes, or Welcome-only tests.

Run original tests and `scripts/check-publication.py` on the entire staged index;
review all added text and screenshots for private paths, account/license data and
proprietary material. Add only reviewed new paths to both publication allowlists.
Commit, create a new annotated immutable Golden tag, push commit/tag, compare local
and remote objects, and verify a clean worktree. Documentation/tooling alone does
not justify another application Golden tag.

## Required network and account regression

Read [NETWORKING.md](NETWORKING.md) before preparing an update. Candidate creation
copies the original networking helpers. The exact-known-build configuration
recipe installs the Ruby bootstrap into a fresh 2026 prefix. Unknown releases
require review of their Ruby path, default trust store and Wine host-root import;
copying a helper does not establish compatibility.

The base evidence template now requires `GENERAL_HTTPS`, `TLS_NEGATIVE_TEST`,
`RUBY_HTTPS`, `CEF_HTML_CALLBACK`, `BROWSER_CALLBACK`, `ACCOUNT_PERSISTENCE`,
`OPTIONAL_ONLINE_SERVICE_REVIEW` and `PLUGIN_HTTPS_REVIEW`. Missing, failed,
untested or deferred **core gates** prevent base acceptance. Review gates pass
only after recording the actual service/plugin matrix; they do not mean every
optional service passes. Separate legal/account requirements for optional services
may be recorded USER_ACTION_DEFERRED without accepting anything for the user.

Compare host, actual container and Windows APIs; test normal Ruby/OpenSSL and
CEF HTTPS plus an HtmlDialog callback. Verify rejection of a controlled untrusted
local certificate. Trigger core login only if needed, with the user personally
handling credentials/legal steps, and verify SketchUp's account UI after the
normal browser callback and clean relaunches. Keep listeners loopback-only;
remove diagnostic servers afterward. Retest painting/DPI/hardware acceleration.
Never publish CA bundles, auth URLs, cookies, tokens, prefix or account screenshots.
The historical application tags are immutable; tooling updates do not retag them.
