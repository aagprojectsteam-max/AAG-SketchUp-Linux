# Maintenance handoff

Use [GOLDEN-STATE.md](GOLDEN-STATE.md), [FINAL-REPORT.md](FINAL-REPORT.md) and [acceptance.json](acceptance.json) as the final state. The original long investigation is preserved in [HISTORY.md](HISTORY.md) and [ROOT-CAUSE.md](ROOT-CAUSE.md); raw evidence and proprietary files remain private.

One canonical root contains app, prefix, private GE-Proton10-25/sniper, configuration and launcher. The production app is 26.1.252 x64. Critical repairs are correct MSVCP140 architecture, native UCRT, complete ProgramData with StyleTemplate.skp, Wine's missing-touch-export fallback, HIGHDPIAWARE at 192 DPI, and Classic 8x MSAA. Steam is not required.

All final GUI and cold-start tests passed; the final rollback is under `backups/final-golden-20260928/installation`. The previous known-good snapshot remains protected. Input Lock was restored to all four device classes locked, mouse acceleration to default and speed to 0.0. Do not unlock or change unrelated input settings for normal launching.

For future changes: back up first, keep original sources, change one component, rerun modeling/save/reopen, Apps/Dock, DPI/mouse, touch-crash and graphics checks. Never kill all Wine sessions. Use the prefix-scoped service. Never publish a prefix, raw dump, source installer, proprietary DLL, credential, private model or account data. A new runtime hash is intentionally rejected by the touch patch until separately validated.

## Hebrew input addition

The current launcher conditionally repairs the demonstrated GNOME/Xwayland US-only map mismatch. Read [HEBREW-INPUT.md](HEBREW-INPUT.md) and [the acceptance matrix](hebrew-input-acceptance.json) before altering input settings. Preserve core networking/account state, the original Goldens and deferred plugin choices. Do not infer core SketchUp failure from the separately documented Xalia auxiliary exception.
