# Validation report — adaptive-planning0.3.0

Observed2026-10-30; public examples/probes are synthetic. Actual personal state, answers, artifacts and account data are excluded.

## Observed checks

- **98 deterministic tests pass**: all70 prior tests unchanged, plus14 export and14 trial regressions. [Actual output](roadmap-0.3.0/unit-results.txt).
- Full JSON Schema independently validates five fixtures and rejects malformed times/date-times. [Result](roadmap-0.3.0/schema-results.txt).
- Independent pinned icalendar7.3.0 parser round-trips Unicode/injection-looking titles, folded CRLF, UTC/DST elapsed time and stable moved UIDs/revisions; no added invitations/alarms/events. [Result](roadmap-0.3.0/calendar-results.txt). Runtime helpers remain Python3.9+ stdlib; developer checks use Python3.10+.
- Trial probes preserve zero versus null, unknown tracking, local observation dates, exact as-of cutoffs, baseline identity and source bytes. Duration samples are not added when their scope may overlap, timing changes do not invent causes, and elapsed dates do not prove outcomes.
- Export probes preserve source bytes and in-progress starts, exclude completed/ended work and existing fixed appointments, retain IDs on move/retry, and refuse changed/symlink/source-alias output. Identical file retry preserves bytes/mtime.

## Independent review and actual instruction use

[Independent report](roadmap-0.3.0/independent-review.md) records exact pre/post probes. Four trial findings were repaired: malformed metadata timestamps escaped structured errors; out-of-window duplicate baseline IDs escaped detection; exact-midnight boundary falsely included an older block; equivalent timestamp spelling appeared as a move. The unchanged independent cases now pass, with corresponding public regressions.

The reviewer authored none of the target and inspected finished helpers/resources. Their separate parser script passed its own hostile-text, repeated-hour, scope, file-output and identity assertions. Actual reviewer-generated responses to general productivity, no-report outcome review and export/reminder requests are preserved. These are bounded instruction-use observations, not native activation telemetry or a separately instrumented comparative model trial. Constructor was requested Sol Medium, reviewer Sol High; executing identity is uninstrumented. Parent integration retained its existing configured selection.

[Frozen criteria](roadmap-0.3.0/criteria.json) preceded implementation. [Before/after CLI results](roadmap-0.3.0/before-after.json) establish the narrow technical addition: the0.2 helper files do not exist, while0.3 executes the requested read-only report/export. This does not claim the earlier conversational skill could not discuss trials, nor prove improved planning effectiveness. The0.2 planning/model comparison remains [historical](report-0.2.0.md).

## Release and remaining limits

Version1/2 state stays compatible; optional trial metadata is validated by its helper within the opaque extension contract. Installing creates no trial, state migration, account connection or background job. A candidate is adopted only after structure/manifest/archive parity, preserved rollback, installed tests, native discovery, exact remote commit readback and GitHub CI.

This release adds local file snapshots, not calendar-client import verification, live reconciliation, two-way vault sync, reminders or cloud storage. Stable UIDs cannot promise duplicate suppression in arbitrary clients; removals do not delete prior imports. Runtime3.9/3.13 is tested by hosted CI before final delivery; local runs use Python3.15 and syntax checks alone do not prove runtime compatibility. Real longitudinal outcomes require future actual reports and are not substituted by synthetic evidence. Capacity remains a bound rather than a joint placement optimizer.
