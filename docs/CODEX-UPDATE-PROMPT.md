# Reusable SketchUp update handoff

Use this prompt with this repository and new legitimate source files. No earlier
conversation is needed. Follow [UPDATE.md](UPDATE.md) for commands and schemas.

## User entrypoint

> SketchUp has an update. My legitimate new installation files are at `<PATH>`.
> Follow this document. Protect the current Golden, create a separate candidate,
> audit changes, reuse only justified fixes, test it, and promote only after all
> mandatory gates pass. Preserve rollback and publish sanitized documentation.

## Instructions for the next session

1. Read `artifacts/current-golden-baseline.json`, `docs/GOLDEN-HISTORY.md`,
   `docs/UPDATE.md`, `docs/ROOT-CAUSE.md`, `docs/WINDOW-PAINTING.md`, `docs/PLUGINS.md`
   and `config/compatibility-rules.json`. Inspect the canonical Apps desktop entry
   to discover the current root. Do not infer private paths from historical logs.
2. Identify complete user-supplied app, content and runtime directories. Record
   legitimate origin, package hashes and separate content version. Sources and
   real Windows remain read-only. Do not download arbitrary DLLs or publish
   application/runtime/plugin payloads, license state, credentials or raw dumps.
3. Protect Base Golden and Plugin Golden independently. Save/close user models
   with authorization. Verify the independent current rollback snapshot and
   desktop entry backups. Do not overwrite an existing root or the only backup.
4. Run `prepare-update.py audit --dry-run` with explicit paths, rollback and
   protected backup roots. Review actual PE build/architecture, all file diffs,
   Qt/CEF/Ruby/VC/UCRT/graphics changes, content completeness, disk and provenance.
   Unknown builds require audit. StringFileInfo may carry a more precise build
   than VS_FIXEDFILEINFO. Do not mistake a filename for a verified version.
5. Start with the known runtime; change one variable at a time. Create a new
   permanent candidate, initialize a fresh prefix and verify actual read-only
   protected mounts inside its container. Its launcher/unit/lock/logs must be
   separate. Do not install or pin its TEST desktop entry as production.
6. Reevaluate old fixes. Keep correct x64 MSVCP. Native UCRT requires evidence.
   Only the exact known missing-export Wine hash permits the strict touch patch.
   An existing native export means no old patch, but still requires behavior
   testing. Re-test DPI/CEF, native viewport, renderer/AA and painting. The optional
   known configuration recipe is limited to an unchanged known-build reinstall;
   changed releases need narrower reviewed engineering. Never patch proprietary
   app code or lower graphics/DPI quality merely to obtain a PASS.
7. Before copying third-party plugins, validate base modeling using a fresh own
   test model, or a copy of the previous fixture. Exercise real GUI tools, save-as,
   reopen, geometry, navigation, input, sharp UI and hardware AA. Repeat every
   first-paint/focus gate, three cold launches, a bounded late-crash observation
   and clean shutdown. Use controlled visual evidence where frameworks/graphics
   changed. Record performance approximately and state benchmark limits.
8. Handle core legal/account/licensing steps with the user in the real visible
   foreground window; never accept, enter credentials or copy Windows activation
   state on their behalf. Optional plugin decisions remain independent. Preserve
   the existing JointPushPull, FredoCorner and V-Ray deferrals unless the user
   explicitly changes them; do not spend time on their licensing or rendering.
9. Only after BASE_PASS, migrate reviewed plugin code individually. Use the
   inventory and dependency ledger. Test native ABI and actual functions/callbacks,
   not toolbar visibility. Keep failed/untested/deferred payloads outside active
   search paths. Optional deferrals do not invalidate base compatibility. A new
   loss of previously needed functionality needs informed user review.
10. Generate the regression template and fill only observed gates with evidence.
    Use base/plugins/ready validation phases. A machine-readable PASS file is a
    reviewer record, not independent proof. Check backward file readability;
    application rollback cannot undo an incompatible save format.
11. Prepare reviewed consistent README/baseline/history/plugin/test/update metadata
    and an unused release tag. Keep the accepted candidate at its tested location.
    Explicitly promote only after READY_FOR_PROMOTION and task authorization.
    The launcher transaction preserves the old installation and journal. Retest
    Apps/Dock/focus/icon/no duplicates and combined model/save behavior, then
    finish the promotion. If it fails, restore recorded launchers and metadata;
    never delete or move historical Golden tags.
12. Keep every meaningful new cause, experiment and limitation in a per-version
    report. Rejected candidates get an explicit rejection reason, production
    impact NONE, retained evidence and a cleanup dry-run. Actual deletion requires
    appropriate exact-path approval and reference checks; no automatic old-Golden
    deletion. Continue routine safe work without unnecessary interruptions.
13. Run meaningful tests, review the entire staged diff, run publication guards,
    commit sanitized sources/docs, create a new immutable tag only for a real
    accepted application release, push, verify remote objects and clean worktree.
    Tooling-only work must not retag the application.

## Completion report

Report candidate/version/runtime, BASE_APPLICATION_COMPATIBILITY and the separate
plugin matrix; reused/removed/new fixes; GUI/graphics/input/painting gates;
performance limits; backward file compatibility; exact active/rollback roots;
promotion or rejection; retained evidence/cleanup scope; commit/tag/remote and
WORKTREE_CLEAN. Do not claim future compatibility or fill unobserved GUI gates.

## Networking requirement for future sessions

Include `docs/NETWORKING.md` in the initial reading. Run the mandatory core network
and account gates from `docs/UPDATE.md`, including a negative TLS test. Reevaluate
both host-to-container/Wine trust and SketchUp's embedded Ruby store after version
changes. Preserve the normal default-browser bridge and host DNS/filter policy.
Optional service terms/login remain USER_ACTION_DEFERRED unless core-required or
explicitly requested. Never repeat a valid login merely to obtain a new screenshot.
Record service limitations honestly and remove all temporary listeners/debugging.
No private CA, browser, credential or session material may enter the public tree.

### Preserve bilingual input

Require normal US/Hebrew switching, exact Unicode in Qt and CEF, English shortcuts after switching back, a new Hebrew filename and model-text save/reopen, pointer accuracy, and Hebrew input after both Apps and Dock cold launches. Inspect the current Xwayland map if the indicator and typed text disagree. Never reset account state or overwrite a custom map blindly. The supported map repair is shared by X11 applications on the current display.
