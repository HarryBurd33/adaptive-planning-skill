# Independent resource contract review

Read candidate core plus planning/adaptation/state references, helper, schema, synthetic template and provenance. Read frozen rubric only after saving actual candidate outputs. This review did not edit the candidate. Helper probes used temporary files only.

## Actionable findings

1. **Model-week shape permits invalid weekdays and dangling task references.** The template with `model_week=[{"weekday":99,"start":"10:00","end":"11:00","task_id":"ghost","label":"invalid weekday"}]` returned exit 0, `valid:true`, empty warnings/errors. The schema lacks weekday maximum and the custom validator does not implement maximum; helper also does not verify the model-week task reference. This goes beyond the disclosed lack of model-week overlap checks: a normal-routine record cannot represent weekday 99. Add explicit 0..6 and task-reference checks (and reject equal/invalid window endpoints), or return an explicit warning that the model-week inventory is unverified. Do not claim checked state has a valid model-week shape while this passes silently.

2. **Historical missed recurrence is reported as current unallocated work.** Starting from valid `examples/initial-state.json` (dated horizon Nov 2–9), append `{id:reading@daily:2026-11-01#1,task_id:reading,period_start:2026-11-01,period_end:2026-11-02,remaining_minutes:30}`. The helper reports `30 minutes unallocated (optional)` and includes it in totals without a historical/outside-horizon marker. The skill correctly forbids automatic habit debt, but retained historical missed habits can look like additional current workload. Prefer classifying totals/warnings by period coverage, or explicitly document that out-of-horizon missed occurrences are historical and must not be rolled into current capacity. The helper does not itself allocate catch-up work, so this is a misleading-result risk rather than observed automatic scheduling.

## Contracts that aligned on reread

- The final `--replace-extension KEY` CLI, digest selected-key set and state reference align. Named extension changes are within the authorized plan; unrelated keys remain protected. Earlier preserve-everything wording was superseded before this report.
- Current/proposed revision CAS, same-ID same-payload duplicate detection, conflicting-ID rejection, completed-block preservation and append-only histories are visible in implementation. These observations are code inspection, not substitutes for the constructor's actual tests.
- `null` versus zero remaining effort is documented and structurally distinct; recurrence IDs use complete anchored local periods, keeping a week intact across month boundaries.
- The template's date/sleep values are explicitly marked synthetic. Core instructions do not import those values as defaults.
- Core instructions preserve the model-week/date-exception distinction and disclose checker limits: no placement solver, capacity budget proof, model-week overlap verification or prose-view comparison. Basic conversational planning is independent of the helper.
- Provenance records immutable Compass revision, inspected paths, adaptation map, monthly additions, MIT/CC BY split and no bundled plugin code. CC-adapted core/planning files are identified separately from MIT original helper material. No unsupported license relicensing was found in inspected provenance.
- Local-link scan found only `validation/report.md` links unresolved while the parent was still authoring that report; recheck after report creation. All other relative Markdown targets resolved at inspection time.

## Execution record and limitations

Saved `.forge/candidate-responses.md` with actual responses for initial, overload, feedback, ambiguity, nonactivation, tool-fallback, fixed-conflict, month-boundary and staged disruption. The staged disruption explicitly distinguishes Tuesday's confirmed completion from Monday's unknown progress and preserves the existing dated plan.

The baseline and candidate use one executor context and inherited history. Parent history already exposed candidate instructions before baseline execution, so superiority comparisons are **inconclusive**. The actual inherited model/effort identity is unknown. No longitudinal personal trial, native skill discovery, real calendar operation or background scheduling was exercised. Parent owns grading against frozen criteria and final integration.

## Final independent re-probes after fixes

Both original findings above are preserved as observations of the earlier candidate. The constructor/parent revised the helper, then this reviewer ran the original probes again independently:

- Invalid weekday 99 now returns exit 2, valid=false, error `$.model_week[0].weekday: above maximum`. A separate weekday=0/unknown task `ghost` probe now also rejects the dangling reference. The two checks are independently discriminating; early schema rejection no longer masks the reference probe.
- The exact historical-reading occurrence appended to valid Nov 2–9 initial state now remains in the input inventory, produces no current unallocated warning, is absent from current `totals`, and appears in `outside_horizon` with relation historical and remaining_minutes 30. Thus it is visible history without being reported as current work debt. Observed check exit was 0.
- Supplemental actual monthly execution is saved in `.forge/monthly-response.md`. It was produced from `examples/initial-state.json` without reading the supplemental expected criteria. It preserves the first-week canonical blocks, explicit later-week uncertainty and full-period boundary distinctions. Parent owns grading.
