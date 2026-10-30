Historical pre-upgrade audit. Version 0.2.0 implementation and evidence are now described in [CHANGELOG.md](CHANGELOG.md) and the [current validation report](adaptive-planning/validation/report.md).

# Update audit — 2026-10-30

Scope confirmed by the user: adaptive-planning plus the Codex desktop app and CLI. Other installed skills/plugins were not included. Observations are a dated snapshot, not an automatic update guarantee.

| Component | Observed status | Evidence/limit |
| --- | --- | --- |
| Codex desktop |26.1027.30824, build22943, production distribution; updater reports `up_to_date` | Native app update check found no eligible configured-channel update. No download, restart or channel change was performed. |
| Standalone Codex CLI |0.166.0 | Both the Homebrew entry point and resolved executable report0.166.0. Homebrew records0.166.0 installed/not outdated; official stable release is rust-v0.166.0, published2026-10-29. |
| App-bundled CLI |0.166.0-alpha.5.1 | Managed as part of the already-current production desktop app. It is not the separately installed stable CLI and was not manually replaced. |
| Global adaptive-planning |0.1.0;31files | Installed files exactly match the reviewed builder and public-checkout skill folders. All package-manifest hashes match. No newer skill-code revision was found on public main at audit intake. |
| GitHub repository |Public; MIT root license;10 relevant topics; v0.1.0 tag | Base main at audit intake: aae62256424499dbdce329c5f4551969471b83cd. Required CC BY4.0 exceptions for Compass-derived instructions remain documented. |
| Current verification |32 deterministic tests pass; release validator passes | Executed again on the unchanged public skill tree; original model-execution/baseline limits remain in the validation report. |

Official stable CLI release: https://github.com/openai/codex/releases/tag/rust-v0.166.0 . The first CLI sample earlier in the audit reported0.165.0; direct repeat reads of both standalone executable paths now consistently report0.166.0. No claim is made that this audit performed that upgrade, and no redundant reinstall was run.

## Observed remaining limitations

- The helper is not a placement optimizer or a full feasibility certificate. It does not compute all deadline-specific capacity, support all sleep exceptions, enforce all elapsed-time preservation or compare prose views.
- Two targeted synthetic probes confirm documented gaps: overlapping model-week windows return `valid:true` without an overlap error; a dependent task can have no dependency-order error when only part of the prerequisite effort was allocated. The latter still reports the prerequisite's unallocated minutes. Inspect warnings and do not call either result fully feasible.
- The original baseline comparison is inconclusive because its executor inherited candidate instructions. One fresh continuity probe worked but was verbose; longitudinal personal outcomes remain untested.
- Full external JSON Schema validation was not part of the original runtime suite. Unknown recurrence progress and schema evolution require careful design rather than invented completion.
- Calendar/Obsidian access, reminder delivery and cross-device personal-state synchronization require actual optional capabilities and authorization.
- Local source isolation must be corrected before code edits: the native worktree tool does not accept the nested checkout as a workspace root in the current chat. This audit leaves the shared local checkout and parent task untouched. The reviewed update is limited to root GitHub documentation; the installed skill tree/version is unchanged.

The ordered remediation plan, assignments and acceptance gates are in [ROADMAP.md](ROADMAP.md). Historical model-execution evidence and limits: [skill validation report](adaptive-planning/validation/report.md). Initial installation/discovery evidence: [VERIFICATION.md](VERIFICATION.md).

## Privacy and scope

No personal planning answers, state files, account configuration, ownership material or private checkpoints are included in this public audit. Personal planning remains local and is not an automatically synchronized account memory. No other skills/plugins, model defaults, services, schedules, accounts or permissions were updated. No feature implementation is claimed by the documentation update.
