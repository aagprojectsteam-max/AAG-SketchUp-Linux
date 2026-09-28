# Update framework report

## Executive summary

UPDATE_FRAMEWORK=PASS for the implemented and tested framework. This does not
claim that an untested future SketchUp release works. Base and Plugin Goldens
remain valid and unchanged. No application upgrade/tag was created for tooling.

## Why the framework exists

Architecture, content, touch exports, CEF/Qt painting and plugin ABI defects
required different evidence. Applying every old workaround blindly would repeat
mistakes. The framework preserves that evidence and separates preparation,
manual validation and production promotion.

## Current Golden baseline

The [sanitized baseline](../artifacts/current-golden-baseline.json) records actual
26.1.252 x64 build, 19 critical file metadata records, runtime/container provenance,
touch state, hardware Classic/MSAA8/192-DPI settings, content and immutable Base
and Plugin tags/commits. Current content audit found 482 files across the recorded
categories; the historical restored set was 481 files. The current full manifest
is the comparison reference, not an assumed historic count.

## Update architecture

[prepare-update.py](../scripts/prepare-update.py) provides audit/create/initialize,
status/template/validate, a separate candidate launcher, explicit promote/finish,
rollback, rejection and cleanup-plan commands. States distinguish creation,
preflight failure, base testing/pass, plugin testing/partial, readiness, promotion,
rejection and rollback. GUI PASS attestations require a named reviewer and
candidate-specific evidence; the tool cannot independently prove visual behavior.

## Candidate isolation

Separate permanent root, fresh prefix, app/content/runtime copies, logs, plugin
state, generated TEST entry and unique unit/lock. No existing Apps/Dock entry
changes during preparation. Actual container mount flags were verified for the
current root, its source subdirectories, the entire backups directory and detected
Windows volume. They were all read-only. Home/session services remain shared;
this is scoped protection rather than a complete security sandbox.

## Source validation

Explicit legitimate input/provenance is required. Symlink/alias destinations,
source/destination overlap, Windows destinations and existing candidate roots are
refused. Copies are hash-verified; source files are not changed. No downloader,
legal acceptance, licensing transfer or proprietary redistribution is included.

## Version detection

Bounded PE StringFileInfo identifies 26.1.252 despite a fixed 26.0.0.0 header.
Conflicting or absent build strings require audit. Tests exercise this real class
of mismatch using original synthetic PE fixtures.

## Architecture audit

App/native modules and critical runtime user32 are audited before execution.
ARM64/x86/unknown app native payloads block automatic preparation. Inactive or new
platform payloads require review, not an automatic exemption. Plugin native
architecture and imports use the existing independent audit tool.

## Critical file diffing

Private reports hold complete relative manifests, hashes, sizes and both sides'
native PE metadata, plus changed/new/missing/unchanged status. Qt, CEF, Ruby,
MSVC/UCRT and graphics files are flagged. Hashes identify provenance/changes;
future app builds do not need to equal today's executable hash.

## Content completeness

StyleTemplate and seven high-value resource categories are checked. Missing
categories fail preflight. Source version is separate and mixed content remains
visible. The current 26.2 restoration is not reused automatically across releases.
New resource layouts may need an evidence-backed rule update.

## Compatibility fix classification

[Rules](../config/compatibility-rules.json) provide the five required classifications,
review versus narrow automatic eligibility, and documentation provenance. Known
unchanged sources use a metadata fast path without bypassing guards or GUI tests.
Unknown builds remain REQUIRES_AUDIT.

## Touch patch eligibility

Four cases are tested: exact known stock/absent export; exact already patched
hash; unknown missing export; future export present. Only the first permits an
explicit strictly guarded patch. An export's presence is not proof of native
correct behavior. Existing stock-export preservation and idempotence tests also
passed against the locally supplied exact stock Wine DLL.

## UCRT/MSVCP policy

Correct x64 MSVCP is retained. Wrong architecture stops preparation until legitimate
correct input is supplied and audited. UCRT is evidence-dependent. The optional
explicit known-build recipe requires unchanged known app/content/runtime, a
reviewed decision for every applied setting and the exact legitimate tested UCRT.
The self-test successfully reproduced this recipe only inside its fresh candidate.

## Runtime upgrade policy

Use the known runtime first; a proven runtime limitation gets another candidate.
Proton/container provenance and file differences are recorded. The framework does
not fetch or automatically upgrade Wine, Mesa or host packages.

## Graphics validation

The design requires supported-engine detection, hardware/API/AA/native-resolution
checks, pointer-safe modeling and relevant screenshot comparisons. PASS here means
the required gates are enforced by the review workflow. No future engine was
validated in this tooling self-test.

## HiDPI validation

The same distinction applies to UI scale, sharpness, Qt/CEF agreement, dialogs,
tray, maximize and hit testing. Future simplification of old DPI settings is
preferred only after actual observed acceptance.

## Plugin revalidation

The generated plan ties Ruby changes to native Ruby ABI, Qt/CEF to dialogs and
callbacks, VC/UCRT to native modules and graphics to renderers. All retained
plugins need a basic smoke test. Base pass precedes migration. Installed untested
or failed plugins cannot pass validation. Optional deferrals remain separate;
new functional losses need informed user review.

## Regression workflow

The template starts every GUI gate NOT_TESTED. The original Ruby geometry source
creates only an empty-model fixture; it does not impersonate mouse/tool tests.
Modeling/save/reopen, file-format review, input, repeated painting/focus, three
cold starts, bounded late-crash checks, performance and clean shutdown are required.
Raw evidence stays private. Legal/account interactions remain the user's actions.

## Promotion

Explicit promotion verifies candidate fingerprint, closed prefixes, rollback,
old desktop target, candidate icon and reviewed canonical metadata hashes. It
refuses an existing tag. Each launcher replacement is atomic; a durable multi-entry
journal supports rollback. A simulated second-entry write failure restored the
first entry. The state waits for real post-promotion GUI evidence before finish.
No real desktop launcher was changed during these tests.

## Rollback

Synthetic promotion/rollback tests restored exact original launcher text and kept
the old root untouched. Real production and independent snapshots remain available.
Power-loss journal recovery and documentation/Git consistency are explicit manual
steps. Application rollback does not guarantee backward file-format readability.

## Candidate cleanup

The current-Golden self-test candidate was rejected intentionally after framework
checks, with production impact NONE. Its cleanup plan proposes only that exact
root and preserves evidence first. It was retained; no new irreversible deletion
was authorized or performed. No automatic old-Golden deletion or retention timer.

## Safety guards

Tests cover production overlap in both directions, existing candidates, aliases,
Windows destinations, missing sources/app/content/runtime, wrong architecture,
insufficient space, output-on-source refusal, changed accepted fingerprints,
foreign evidence, missing gates, tag immutability, partial plugin states and
unsafe dry-run use on mutating commands.

## Automated tests

47 Python tests passed: 38 update-workflow tests plus nine launcher/plugin/touch
checks, including the optional exact-stock Wine integration test. The prior plugin
release's C popup probe also passed against the installed helper. Test fixtures
contain original synthetic metadata, never proprietary binaries.

## Self-test results

A read-only audit of the current Golden identified 26.1.252, x64 MSVCP, UCRT,
patched touch state, content, DPI and graphics preferences, with no application
or content differences. Estimated candidate space was about 6.11 GiB including
2 GiB prefix allowance; over 2 TB was available. Full source copies were verified,
a fresh prefix initialized and actual read-only mounts checked. The optional
known-settings recipe rebuilt the identical local popup helper hash.

Two implementation faults were caught: the minimal environment initially omitted
HOME, then omitted the known GE non-Steam flags. Both were fixed and covered by a
regression test. The failed partial prefix/logs remain private; only that test
prefix's processes were stopped. No SketchUp legal dialog or GUI acceptance was
claimed. The successful prefix initialization closed with zero remaining processes.

After all self-test runtime work, every one of the production installation's
40,254 regular files and 3,591 symlink targets still matched the final Plugin
Golden snapshot. The current root was not launched or modified by the framework.
The self-test candidate's modeling/plugin gates remain NOT_TESTED, and it was
never ready for promotion. Rejection and cleanup-plan commands were exercised.

## Future Codex workflow

[CODEX-UPDATE-PROMPT.md](CODEX-UPDATE-PROMPT.md) provides a standalone handoff with
source discovery, audits, conditional fixes, isolated testing, promotion/rejection,
rollback, privacy and publication. [UPDATE.md](UPDATE.md) supplies commands,
arguments, schemas, path discovery and recovery without this conversation.

## Known limitations

AUTOMATED: file/version/architecture/content/runtime audits, protected-path guards,
copy verification, exact patch eligibility, metadata/state checks and journaled
launcher changes. REQUIRES HUMAN VALIDATION: visual/UI/input/graphics quality,
actual tools/plugins, legal/account actions, performance interpretation, metadata
meaning and file-format tradeoffs. REQUIRES NEW ENGINEERING IF CHANGED: runtime
layout/behavior, new graphics/content architecture, unknown dependency and window
painting assumptions. A PASS JSON remains a reviewed record, not independent proof.
No future-release compatibility guarantee or automatic Windows installer extraction.

## GitHub publication

Tooling is committed separately as `feat: add safe SketchUp update workflow`.
No new application tag is created; both existing tag objects/commits remain fixed.
Only original code, documentation and metadata are allowlisted. The full staged
index is checked for proprietary binaries/archives, secrets and private paths.
The final local receipt records pushed commit, remote equality and clean worktree.
The [machine-readable matrix](update-framework-acceptance.json) records scope and
technical gate results; future GUI acceptance is explicitly outside this self-test.
