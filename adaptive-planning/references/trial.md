# Optional real-use trial

A trial is requested use with reported experience, not a synthetic success claim or a background service. Agree a short period (propose one week; two only if useful), save a baseline and identify unresolved assumptions. Never require a trial for ordinary planning. Do not change declared sleep or required commitments to make the baseline fit.

Keep this private in the existing state, outside the installed skill and all public repositories. Version1 and2 both support an opaque `extensions.trial` record; this feature does not require migration. Use the current revision, a stable update ID and `--replace-extension trial` through the [state protocol](state.md). Preserve history and existing review IDs. Correct a provisional baseline before the trial begins when the user supplies missing constraints; after it starts, retain the baseline for comparison. Save later trials separately rather than erasing the prior observations.

## Record

The report reads these fields:

- `id`: nonempty stable trial identifier.
- `start_date`, `end_date`: local YYYY-MM-DD, exclusive end; positive range at most366 days. One week is the proposed starting length, not a required minimum.
- `baseline_revision`: nonnegative integer no greater than the current revision. When creating the snapshot as part of a commit, name its resulting revision.
- `baseline_blocks`: explicit list copied from the canonical blocks. Retain stable IDs and start/end timestamps; the normal full block records are suitable. The report requires unique nonempty IDs and valid positive intervals, including records outside the trial window.
- `reviews`: optional list, empty when no review was reported. Each review has nonempty unique `id` and aware `observed_at`; optional `burden_minutes` is null or finite nonnegative minutes, `helped` is null or a boolean, `reason` and `note` are null or text. Zero burden and helped=false are real reported values. No response stays unknown.

Store work progress in the existing `progress` ledger and narrative experiences in `feedback`, preserving the evidence IDs. `actual_minutes` is a reported sample with its scope explained in the note; partial effort is not a completed-task duration. Do not decrement remaining effort just because a planned slot ended. Updates retry through the existing state idempotency contract, never by applying the same progress twice. This optional metadata is validated by the trial helper, not by the base schema's opaque extension contract.

## Check in and review

An optional brief check-in can ask what was done and the actual duration, why anything moved, how burdensome planning felt, and whether a change helped. The person may report only what is useful. Daily check-ins and an end-of-week review are alternatives, not prerequisites for one another. Record their words without scores or guesses about motivation. Evidence-backed changes remain reversible with before/after values and undo IDs; one disruption does not establish a lasting preference. See [adaptation](adaptation.md).

Run `python3 scripts/planning_trial.py STATE --as-of AWARE_TIMESTAMP` from the skill folder. It only reads state and emits JSON. No file, calendar or schedule is written. Invalid state or trial metadata returns valid=false/exit2. Missing trial metadata returns configured=false rather than inventing a study. The report includes trial/revision/timezone, local days, recorded progress/duration samples, feedback/reviews, same-ID timing changes, absent baseline IDs, future planned minutes, and checker warnings.

Only observations recorded by the supplied as-of instant and inside the trial dates appear. Days use the observation's local reporting date, not an inferred work date. Future days are `future`, an unreported current day is `awaiting-report`, older days with no observation are `unreported`, and days with any observation are `reported`; these describe reporting only. `window-ended` means dates elapsed, not goals met. Raw duration samples are not added because their scope may overlap. A removed block is not automatically a miss; a timing change alone gives no cause. These are observations, not a completion score, evidence of health benefits or a causal effectiveness study.

A real trial remains pending until the dates and actual feedback occur. The helper's synthetic tests cannot substitute for that experience. Optional reminders require a real scheduler, explicit timing and authorization. Local files do not create cloud sync or automatic cross-chat memory.
