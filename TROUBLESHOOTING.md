# Troubleshooting

Start with the installation's self-check and local diagnostic report:

```bash
"$SKETCHUP_ROOT/bin/launch-sketchup.py" --check
"$SKETCHUP_ROOT/bin/collect-diagnostics.py"
"$SKETCHUP_ROOT/bin/launch-sketchup.py" --debug
```

| Symptom | First check |
| --- | --- |
| No startup / c000007b | Correct x64 MSVCP140 in both app and prefix; inspect required-file check |
| Embedded Ruby exits | Verified native x64 UCRT and native,builtin override |
| Welcome works, model creation crashes | ProgramData Styles/StyleTemplate.skp and complete bundled content |
| Direct touch causes BugSplat | Exact Wine user32 touch-export fallback; no full multitouch support |
| Black/partial Welcome or tiny UI | 192 DPI plus prefix HIGHDPIAWARE; avoid stacked Qt scale variables |
| Jagged viewport | Classic graphics, 8x MSAA, full restart and native framebuffer dimensions |
| Incorrect mouse hits | Verify actual application coordinates; avoid mixing X11 warps with Wayland clicks |
| Duplicate Dock icon | Pin the canonical aag-sketchup-2026.desktop entry with steam_app_0 matching |
| Steam unexpectedly starts | Old URI jobs, autostart entries or saved session records; Steam is not required |
| Stale processes | Inspect only the canonical prefix and its user systemd service |
| Model will not reopen | Preserve original and backup; compare same app/runtime/content and inspect logs |

See the [complete troubleshooting guide](docs/TROUBLESHOOTING.md) for diagnostics and recovery, and [root causes](docs/ROOT-CAUSE.md) for hashes and evidence.

Save work and back up before changes. Do not globally kill Wine: unrelated applications may be running. Review logs before sharing; raw dumps, account data and models do not belong in the public repository. Runtime/app/driver updates require a new regression run.
