# Independent review: adaptive-planning 0.3.0

Initial code review, 2026-10-30. Requested assignment: Sol / High. Actual executing model/effort identity was not instrumented; no claim that this assignment ran under that identity. Candidate and frozen criteria were read only; no personal state or other private runs read. Only this report and temporary synthetic probes were written. No external services or Git operations.

## Initial result: four trial defects require repair

All repros below use Python `-B`, `sys.path.insert(0, '<checkout>/adaptive-planning/scripts')`, `from planning_trial import trial_report`, and this exact synthetic fixture:

```python
import copy, json
from pathlib import Path
ROOT = Path('<checkout>/adaptive-planning')
def fixture():
    s = json.loads((ROOT/'templates/state.json').read_text())
    s['profile']['sleep'] = None
    s['dated_plan'].update(start='2026-11-02', end='2026-11-05')
    s['tasks'] = [dict(id='w', title='Work', remaining_minutes=180,
        deadline=None, preferred_date=None, priority='high', required=True,
        flexible=True, dependencies=[], min_session_minutes=30, recurrence=None)]
    s['dated_plan']['blocks'] = [dict(id='b', task_id='w', occurrence_id=None,
        status='planned', start='2026-11-02T10:00:00-07:00',
        end='2026-11-02T11:00:00-07:00')]
    s['extensions']['trial'] = dict(id='t', start_date='2026-11-02',
        end_date='2026-11-05', baseline_revision=0,
        baseline_blocks=copy.deepcopy(s['dated_plan']['blocks']), reviews=[])
    return s
AS = '2026-11-03T12:00:00-07:00'
```

1. **P2: malformed extension timestamps escape the validation result.** `planning_trial.py:40,53,98`.

   Reproduction A: `s=fixture(); s['extensions']['trial']['baseline_blocks'][0]['start']=None; trial_report(s, AS)`.
   Reproduction B: `s=fixture(); s['extensions']['trial']['reviews']=[dict(id='r', observed_at=None)]; trial_report(s, AS)`.
   Actual for both: raises `AttributeError: 'NoneType' object has no attribute 'replace'`.
   Expected: structured `valid:false` trial error; CLI exit 2 with JSON, no traceback. The catch omits AttributeError and stamp assumes string input. Explicit type validation would give better errors. Null start_date/end_date already return invalid correctly.

2. **P2: duplicate baseline identities escape validation when the first block is outside the window.** `planning_trial.py:36-44`.

   ```python
   s=fixture()
   old=copy.deepcopy(s['extensions']['trial']['baseline_blocks'][0])
   old.update(start='2026-10-31T10:00:00-06:00', end='2026-10-31T11:00:00-06:00')
   s['extensions']['trial']['baseline_blocks'].insert(0, old)
   r=trial_report(s, AS)
   ```
   Actual `r['valid'] is True`, despite duplicate `b` IDs. Expected invalid metadata. Duplicate detection uses the filtered `old` mapping rather than all seen baseline IDs; reject all duplicates before filtering.

3. **P2: a baseline block entirely before the trial is reported as absent in the trial.** `planning_trial.py:43`.

   ```python
   s=fixture()
   s['extensions']['trial']['baseline_blocks']=[dict(id='old-midnight',
       start='2026-11-01T23:00:00-07:00', end='2026-11-02T00:00:00-07:00')]
   r=trial_report(s, AS)
   ```
   Actual `baseline_block_ids_absent_now == ['old-midnight']`. Expected `[]`: the block ends exactly at the exclusive trial-start boundary and never overlaps the trial. Compare actual aware window instants with strict intersection, not inclusive end calendar dates.

4. **P2: equivalent timestamp spellings invent a recorded move.** `planning_trial.py:79-82`.

   ```python
   s=fixture()
   s['extensions']['trial']['baseline_blocks'][0].update(
       start='2026-11-02T10:00-07:00', end='2026-11-02T11:00-07:00')
   r=trial_report(s, AS)
   ```
   Actual: moved_blocks contains `b`, before 10:00/11:00 and after 10:00:00/11:00:00. Expected `[]`: identical instants and duration. Normalize timestamps for comparison while preserving original strings in genuine before/after evidence.

## Actual validation already completed

Original regressions run independently from repository skill directory, Python 3.15.0:

```
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s validation -p 'test_state.py'          # 30 pass
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s validation -p 'test_capacity.py'       # 17 pass
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s validation -p 'test_examples.py'       # 2 pass
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s validation -p 'test_upgrade_state.py'  # 21 pass
```

70 original tests passed. Python 3.9 runtime was not found by `command -v python3.9`; this is not an actual 3.9 runtime pass.

Held-out script: `/private/tmp/adaptive-review-probes.py`; invoke `PYTHONDONTWRITEBYTECODE=1 python3 -B /private/tmp/adaptive-review-probes.py`. This script prints defects rather than considering them passing. It asserts unchanged synthetic input objects and has actual assertion gates for the following export cases:

- Repeated-hour block start `2026-11-01T01:55:00-06:00`, end `2026-11-01T01:25:00-07:00`, cutoff `01:59-06:00`: DTSTART `20261101T075500Z`, DTEND `20261101T082500Z`; original start retained, 30 real elapsed minutes.
- Title `'🌱'*70 + '\\,;\r\nBEGIN:VEVENT\nATTENDEE:evil\nBEGIN:VALARM'`: every physical UTF-8 line at most 75 octets; only one VEVENT; no logical VALARM; deterministic retry.
- Revision 1 plus moved same block: stable UID, SEQUENCE 1, DTSTAMP `20261102T160000Z`. Another plan_id: distinct UID.
- Exclusive output: identical retry leaves mtime unchanged; rejects source path, hardlink to source, valid and dangling symlink, FIFO, and changed existing content. All checked source/target bytes preserved.
- Raw trial sample cutoff: progress at `2026-11-03T02:00:00+00:00` with actual 120 is attached to Denver November 2; sample exactly at cutoff with actual 0 survives; sample one microsecond after cutoff and later sample are excluded. No source-object mutation.
- Invalid top-level `{}`, `None`, `[]`, and wrong-type extensions return invalid. Null start_date/end_date reject. A 366-day trial range is allowed by the helper contract (the temporary script's label `367-day-range` is inaccurate; 2026-01-01 to 2027-01-02 is exactly 366 days).

## Limits / pending gates

No independent RFC parser was available in this worker's configured environment yet. Export syntax probes used independent assertions but not a third-party parse round-trip. Parent is adding the pinned development parser separately. No actual calendar import or services were exercised or authorized. Runtime implementation remains stdlib.

Docs/SKILL and actual model-use activation cases are still being authored by parent and have not been reviewed. Initial review does not establish a complete acceptance pass. One bounded re-probe remains after fixes, then documentation and activation review as assigned.

## Bounded post-repair re-probe

Reran the unchanged `/private/tmp/adaptive-review-probes.py` against repaired source. Full stdout retained temporarily at `/private/tmp/adaptive-review-reprobe.out`.

- Null baseline start and null review observed_at: now return `valid:false`, `errors:["invalid trial: 'NoneType' object has no attribute 'replace'"]`; no exception escapes. Initial finding 1 resolved.
- Duplicate baseline ID with first item outside window: now `valid:false`, `errors:["invalid trial: trial baseline block ids must be nonempty and unique"]`. Finding 2 resolved.
- Baseline ending at exact trial start: now `valid:true`, `baseline_block_ids_absent_now:[]`, `moved_blocks:[]`. Finding 3 resolved.
- Equivalent timestamp spellings: now `valid:true`, `moved_blocks:[]`. Finding 4 resolved.
- Exact cutoff/local-date/raw-duration assertions unchanged: samples remain `[120,0]`, future data excluded, object unchanged.
- Independent ICS identity/DST/folding/injection and exclusive output probes all passed unchanged.

Also actually ran `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s validation` from the repository skill directory: **98 tests passed**, including the original 70. No further helper defect found within these bounded probes. Documentation, activation cases, independent parser, and Python 3.9 runtime qualification remain separate gates as noted above.

## Finished documentation and independent parser review

Read current `SKILL.md` version 0.3.0, `references/trial.md`, and `references/exports.md` against repaired helper behavior. No unresolved documentation/helper mismatch found in this bounded review. Instructions correctly exclude incidental dates and general productivity advice from activation; trial setup remains optional; no observations means no outcome inference; warnings remain visible; exports are local snapshots; duplicate import/update behavior varies by calendar client; removals do not delete prior imports; no reminders, live writes, or two-way synchronization are promised.

Ran a newly authored independent parser probe, **not** the parent's calendar validator:

```
PYTHONDONTWRITEBYTECODE=1 '<checkout>/.venv/bin/python' -B /private/tmp/adaptive-review-parser.py
```

Actual output: `Independent parser 7.3.0 PASS: title round-trip, one event, UTC/repeated hour/original start, completed/past/fixed exclusions, no alarms/invites, identity/revision/determinism, unchanged input`.

Inputs: title `'独立🌱'*48+'\\,;\r\nBEGIN:VEVENT\nATTENDEE:evil\nBEGIN:VALARM'`; repeated-hour work block 2026-11-01 01:55-06:00 through 01:25-07:00; cutoff 01:59-06:00; additional completed block, ended-unreported block, and fixed appointment. Independent `icalendar.Calendar.from_ical` returned exactly one event and the original title with CRLF normalized to LF, no alarm components, precisely UID/DTSTAMP/DTSTART/DTEND/SUMMARY/SEQUENCE/DESCRIPTION properties. UTC instants were 07:55Z and 08:25Z (30 elapsed minutes), preserving original start. Retry stable; actual moved revision retained UID with SEQUENCE1 and changed DTSTAMP; different plan changed UID. Source object stayed equal to its copy. This independently closes parser and scope probes without live-provider claims.

Both helper sources also parse using Python 3.9 grammar (`ast.parse(..., feature_version=(3,9))`); this is explicitly syntax-only, not a 3.9 runtime qualification.

## Actual activation responses generated in this review

These are the reviewer's actual generated responses to the three supplied synthetic requests, captured now after reading the skill. They are not a simulated report of responses from a separately instrumented model or fresh host runtime. They establish this bounded instruction-following observation only. No separate model identity/effort has been verified.

### Request A

> What makes a habit stick? My birthday is Monday.

**Actual response:** Pick a small action, attach it to a familiar cue, and make it easy to start. For example: after breakfast, read one page. Keep the materials ready and choose a minimum you can manage on a busy day. If you miss a day, return at the next opportunity; you don't need to make up a debt. Your birthday can be a useful starting cue if you want one.

**Observed gate:** Direct general answer; no planning horizon, timezone, saved-state search, trial intake, reminder, or calendar action requested or performed.

### Request B

> My saved state has no trial metadata and no progress. Summarize whether planning improved my outcomes.

**Actual response:** The saved state doesn't establish whether planning improved your outcomes. With no trial baseline or progress reports, completion, actual time spent, and benefits remain unknown. The lack of reports also doesn't establish failure. You can review any experience you remember, but the existing records don't support an improvement claim.

**Actual execution supporting response:** `/private/tmp/adaptive-review-parser.py` constructed only a synthetic saved state from the public template, with no trial extension and empty progress, then called `trial_report`. Observed `valid:true`, `configured:false`, message `No trial metadata recorded; no trial results can be inferred.` Warnings remained explicit (sleep unknown, 120 minutes unallocated). No personal state was accessed.

### Request C

> Export my saved plan as an Obsidian note and calendar file. Does that mean I have reminders and my existing calendar will update without duplicates?

**Actual response:** Created the note and calendar file from the supplied synthetic saved plan: `/private/tmp/adaptive-activation-review/proposed-plan.md` and `/private/tmp/adaptive-activation-review/proposed-plan.ics`. These are local snapshots. They create no reminders and make no changes to your existing calendar. Stable event IDs help identify the same block, but your calendar client's import behavior determines whether it updates events or creates duplicates. Removed blocks also won't delete earlier imports. The plan still has unconfirmed sleep constraints and 120 unallocated minutes, so the export doesn't certify feasibility.

**Actual execution supporting response:** The independent parser probe wrote exactly those two temporary private artifacts through `write_output`: Markdown832 bytes, ICS467 bytes. Verified their bytes match rendered results and the synthetic source state's SHA256 remained unchanged. No vault discovery, live calendar write, reminder, scheduler, or network operation occurred. The response explicitly labels the synthetic source rather than pretending personal saved data was read.

## Review disposition

All four initial P2 helper findings were repaired and independently re-probed. Original70 and complete98 tests passed. Independent parser round-trip, export identity/scope/UTC/DST/folding/injection/output preservation, trial evidence/missing/zero/cutoff/local-date/read-only probes, finished docs review, and the three bounded actual activation responses are recorded above. No unresolved critical defect found within this review scope. Actual Python3.9 runtime, calendar-client imports, delivery, and a real-use trial remain untested and must not be advertised as verified.
