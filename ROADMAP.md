# Adaptive Planning roadmap

Audit date: 2026-10-30 (America/Denver). This is a prioritized implementation and verification plan, not a claim that the proposed features are delivered. Historical pre-implementation release: 0.1.0; current technical release: 0.3.0. Basic conversational planning already works; the optional helper checks a documented subset of constraints.

## Version0.3.0 continuation

Step4 now has a private baseline/review contract and a read-only trial report. Synthetic tests verify unknown/zero reports, elapsed dates, stable timing comparisons and local reporting dates. Actual longitudinal outcomes still require the agreed dates and real reported experience; none are published or inferred.

Step5 now has local iCalendar and Markdown/Obsidian artifact adapters with stable block IDs, UTC dates, escaping, explicit as-of filtering and safe output retries. They are file snapshots, not connected-provider synchronization. A separate pinned parser checks the calendar format. A live calendar connector, two-way vault sync, reminder delivery and multi-device private storage are still unimplemented/unverified.

Next gates: gather missing personal constraints privately, use the saved baseline during the trial period, review reported effort/burden/changes after actual use, then select and connect a provider for exact authorized operations and duplicate/uncertain-outcome tests. A native scheduler exists on supported hosts, but installation creates no job; timing and delivery require a separate requested reminder. Provider/account choices and data-access permission are not inferred from an export request.

## Version 0.2.0 implementation status

The technical release implements the scheduling/state/capacity/schema/handoff work below. A standalone checkout was created outside the shared task root through the approved filesystem boundary; the native chat root was not changed. The repository code and branch now live in that independent checkout, while the original task checkpoint is reused. Native workspace attachment remains an optional host UI step, not a claim made by the shell working directory.

- Step 2a: implemented circular overlap checks and full/transitive prerequisite readiness, with regressions.
- Step 2b: implemented explicit capacity bounds, version-2 sleep overrides, deterministic as-of preservation, canonical data views, and a pinned independent schema check. The helper remains a bound/checker, not a joint placement optimizer or prose reviewer.
- Step 3: completed one separate-context matched baseline/candidate round and independent resource review. Executing identity is not independently instrumented; no general superiority claim is made.
- Step 4: added concise handoff guidance/template and tested continuity. A consented real-person longitudinal trial remains pending actual use and feedback.
- Step 5 at0.2: optional integrations were unimplemented. Version0.3 adds portable file adapters only; live services remain subject to the gates above.

See [the current validation report](adaptive-planning/validation/report.md) and [CHANGELOG.md](CHANGELOG.md). The sections below retain the original plan and acceptance gates for traceability; they must not be read as claiming every future optional feature is shipped.

## 1. Establish a safe maintenance workspace (P0; prerequisite for code changes)

**Limitation:** the current local publishing checkout sits beneath a shared task root. The native worktree tool rejects that nested source because it is not an attached workspace root. A changed shell directory or new nested Git repository does not establish chat isolation.

**Next action:** add the existing adaptive-planning repository as this chat's workspace root, or open it as its own Codex project; then create/reuse a managed worktree outside the shared task root. Fast-forward the local checkout to the verified public main. Preserve the original checkpoint store and personal planning state; do not take another task's lease or change parent ignores.

**Gate:** native metadata confirms the intended root, source Git HEAD and active worktree; current jobs/ownership are reconciled; a checkpoint/portable handoff verifies. Read-only audits and remote documentation updates can be completed before that code-work boundary. Review: Sol Medium for bounded setup; Astra Extra High only on ownership/source conflicts.

## 2. Strengthen deterministic checks (P1; after step1, two bounded packages)

### 2a. Model-week overlap and dependency completion

- Add local-wall-time model-week overlap checking, including Sunday-to-Monday wrap. Do not pretend an undated model week determines DST-specific dated offsets.
- Check that all known remaining prerequisite effort is completed or validly allocated before dependent work begins; ordering the currently allocated fraction alone is insufficient.
- Decide and document how unknown prerequisite effort is reported. Unknown cannot become satisfied by omission.

**Discriminating inputs:** Monday08:30–09:30 and09:00–10:00 must flag overlap; touching09:30 endpoints must pass. Sunday23:30–Monday01:00 versus Monday00:30–01:30 must flag overlap. TaskA needs120m but has only60m planned; taskB depends onA and begins after those60m: B must not be certified ready. Contrast with A fully covered beforeB and with unknown remaining effort.

**Gate:** new failing-before/passing-after regressions, all existing32 tests, separate contract review, and preserved state/history. Keep `valid` scoped to checked constraints; show unmet/unknown requirements explicitly. Assignment: Sol Medium implementation; Sol High/Astra Extra High review if semantics remain ambiguous.

### 2b. Capacity, protected-time exceptions and multi-scale consistency

- Add a small capacity-report utility only if it materially reduces manual arithmetic. Use explicit availability, union of protected/fixed intervals, meals/transitions/free time, then stated buffers. Compute deadline-specific eligible minutes and minimum-session gaps; do not build a separate optimizer by default.
- Design a backward-compatible representation for sleep exceptions/multiple protected windows. Never change a user's sleep to make work fit.
- Define a trustworthy as-of-time rule for elapsed and partially completed blocks; preserve history on revision.
- Add independent full-schema validation in CI using a pinned development-only validator. Keep runtime planning usable without a new dependency.
- Add property/fixture checks that daily, weekly and monthly views derive from one occurrence/block inventory. Preserve cross-month weeks, DST and unknown-versus-zero distinctions.

**Discriminating inputs:**8h required versus4h usable must yield4h shortfall; overlapping protected periods must be subtracted once; a15m gap cannot fit a30m minimum; a sleep exception must not silently remove normal protection elsewhere; one weekly occurrence spanning Oct26–Nov2 stays one quota in both months. Partial progress retried twice stays applied once.

**Gate:** fixed semantics approved in the implementation brief, explicit schema version/migration if needed, regression tests before code, preservation/rollback of old state, and a reviewed capacity report that cannot label warnings as feasibility. Assignment: Sol Medium code; Astra Extra High design/review for changed constraint semantics.

## 3. Run a clean behavioral evaluation (P1; can follow step1 independently of step2)

**Limitation:** the original direct-prompt baseline inherited candidate instructions, so comparative benefit is inconclusive. Exact executing model/effort was not observable. A fresh-context continuity probe passed once but does not establish long-term effectiveness.

**Plan:** freeze supplied acceptance cases and held-out disruptions before execution. Run baseline and candidate in separate fresh contexts with identical tools, exact observed model/effort, and bounded effort. Include initial planning, staged disruption/partial progress, feedback, overload, fresh-state resume, ambiguous deadlines, missing tools and a non-activation request. Use an evaluator that did not author the candidate; retain actual outputs and criteria hashes.

**Gate:** no hard-constraint violation, fabricated completion/availability, unsupported tool action or stale overwrite; correct effort/recurrence totals or explicit unmet work. Report pass/fail/inconclusive per case. Do not infer causal improvement from a small or contaminated sample. Budget first: one matched baseline/candidate round, one repair round if justified, no paid API fallback. Assignment: exact model chosen from the live catalog; bounded executors plus independent stronger review only when delegation is permitted.

## 4. Make continuity shorter and try real use (P2; after basic evaluation)

- Add a concise default handoff target (about250–350 words, full JSON only when needed) while preserving IDs, remaining effort, hard constraints, adaptations/undo, provenance and unresolved assumptions.
- Collect a consented one- or two-week personal trial: reported actual durations, why blocks moved, user burden, unmet work, and whether adjustments helped. Missing tracking remains unknown; no grading or penalties.
- Separate tentative patterns and one-off disruptions from durable reversible preferences. Reject unsupported claims about model retraining or guaranteed sustainable outcomes.

**Gate:** a different chat can resume from the short handoff without losing progress or creating habit debt; the user can undo every consequential adaptation; report observations and limits rather than a universal success claim. Assignment: Sol Medium; specialist review only if output format requires it.

## 5. Optional integrations (P3; separate user choice/authorization)

Calendar/Obsidian adapters and automatic check-ins are not built-in capabilities. If requested later, verify a real connector/scheduler, preview exact external operations, use stable external IDs, inspect uncertain outcomes before retries, and test duplicate suppression. Reminders require a real scheduler and authorization; installing the skill alone creates none. Multi-device continuity additionally needs an approved private storage/synchronization mechanism; never use this public repository for personal plans.

**Gate:** connector-specific read/write/retry/permission tests and actual scheduler delivery evidence. No account connections, events or background jobs are created by this roadmap.

## Personal planning next step

A real weekly plan requires the user's sleep/wake preferences, fixed commitments/travel, confirmed available windows, tasks/deadlines/remaining effort/priorities, recurring activities and desired free time. Those inputs must come from the user. Keep all personal answers/state private and separate from this repository. Completing that intake is use of the existing skill, not an implementation prerequisite for every other user.

## Release gate for any behavior change

Freeze scope and regressions, preserve prior files/state, implement in the verified workspace, run deterministic checks plus relevant actual model examples, reconcile independent findings, refresh evidence hashes/manifests and matching ZIP, bump the skill version, publish to the authorized repository, update only an unmodified global copy, and verify native discovery and exact installed/published parity. A passing process exit or confidence is not sufficient evidence. Version 0.1.0 remains the rollback baseline; version 0.2.0 is adopted only after the documented gate passes.
