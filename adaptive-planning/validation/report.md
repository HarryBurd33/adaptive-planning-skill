# Validation report — adaptive-planning 0.2.0

Observed 2026-10-30 America/Denver. Synthetic data only. This is an incremental technical release; it does not establish long-term personal outcomes or add external integrations.

## Executed checks

- **70 deterministic tests pass**: all32 original tests retained, plus38 scheduling/capacity/state-upgrade regressions. [Actual console output](upgrade-0.2.0/unit-results.txt).
- Independent full JSON Schema validation passes for the template and all three example states (four fixtures), with invalid HH:MM and date-time inputs rejected. Development-only jsonschema4.26.0 plus rfc3339-validator0.1.4 are pinned; Python3.10+ is used for that developer check. Runtime helpers remain Python3.9+ standard library/IANA data. [Actual result](upgrade-0.2.0/full-schema-results.txt).
- [Paired before/after probes](upgrade-0.2.0/before-after.json) demonstrate benefit on identical data:0.1 accepts model-week overlaps and incomplete known prerequisite allocation;0.2 rejects both.0.1 falsely rejects overlapping generic reservation layers;0.2 unions them while retaining actual-appointment/task conflict errors.
- Coverage includes Sunday wrap/touching intervals, transitive unknown/blocked readiness, no double buffer charge, missing availability versus zero, missing required recurrence inventory versus zero, long earlier sleep anchors, DST/cross-month view conservation, deadline/minimum-session bounds, as-of history preservation and retry contracts, version1->2 lossless upgrade/downgrade rejection, and existing progress/history/extension integrity.

## Independent findings and repairs

Constructor review of the independently authored capacity utility reproduced three issues: a long sleep exception anchored before the horizon was omitted; a percentage was incorrectly charged again inside each task deadline window; missing required occurrence inventory appeared as zero required effort. Exact regression cases now pass. A separate reviewer reproduced false invalidation of overlapping generic protection; that acceptance interpretation was clarified before final repair. Actual meetings/tasks still conflict. Parent review additionally required transitive readiness propagation. All prior regressions remained intact. [Independent review and final re-probe](upgrade-0.2.0/independent-review.md).

The generic-protection clarification was an evaluation-design correction, not permission to suppress actual collision errors: protection10–12 plus11–13 reserves three hours once; two fixed meetings at those times still fail. The old source was rerun under that clarified criterion before final candidate assessment. Frozen original criteria plus discriminating supplemental probes were used; no failing gate was removed to admit a candidate.

## Actual separate-context model comparison

Baseline0.1 and candidate0.2 executors each started without inherited task history, read only their assigned skill and the same request inputs, and did not read one another's outputs or the evaluator criteria before responding. Both were explicitly assigned gpt-6.1-sol/medium. Executing model/effort was not independently instrumented; configured assignment is not per-turn telemetry. Each arm used one context across its staged/independent probes, so cases within an arm are not independently randomized.

[Baseline outputs](upgrade-0.2.0/baseline-responses.md) and [candidate outputs](upgrade-0.2.0/candidate-responses.md) cover the supplied initial plan, staged disruption, feedback, overload, nonactivation and saved-state continuity. Parent reviewed both against [frozen criteria](upgrade-0.2.0/criteria.json). Both preserve the tested sleep/fixed constraints, correct paper/recurrence totals or explicit unmet work, Tuesday's confirmed progress, missing-data uncertainty, reversible adaptations, and model-week/dated-exception distinction. No false file/calendar/reminder action is claimed. Candidate's portable continuity rendering is shorter; [word counts](upgrade-0.2.0/handoff-word-counts.json) record the narrow observation. This small non-blinded sample does not prove general planning superiority; deterministic before/after defects are the demonstrated technical benefit.

## Compatibility, limits and release gate

Version1 state stays readable, and no personal planning file is migrated during installation. Extended availability/sleep constraints require a version2 proposal with revision/idempotency protection; downgrade is rejected. Without explicit as-of, legacy behavior remains compatible and elapsed preservation is warned as unverified. Capacity figures are shared upper bounds, not a placement solver or a universal feasibility certificate. Unknown availability/effort/occurrence inventory stays unknown; later/full-period demand is not compressed into a partial view. Human verification of preferences, real availability and transitions remains necessary.

No calendar/Obsidian connection, reminders, automatic background planning, private-state cloud sync, or real-person longitudinal trial is claimed. Those require separate capabilities/authorization or user inputs. The release gate is regression/full-schema/structure success, reviewed source, matching package/installed bytes, preserved rollback, and verified GitHub CI. Original0.1 evidence remains [historical](report-0.1.0.md); its contaminated baseline is not reused as a clean comparison.
