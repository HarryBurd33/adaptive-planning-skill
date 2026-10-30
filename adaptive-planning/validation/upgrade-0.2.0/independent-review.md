# Independent candidate review

Requested reviewer execution gpt-6.1-sol/medium; actual runtime model/effort is not independently verifiable. I authored none of the candidate helper, schema or resources. Candidate responses were saved before reading frozen criteria. No baseline outputs were read. Review is bounded, read-only, and uses only synthetic temporary in-memory states; no candidate or planning-state file was edited.

Reviewed SKILL.md; references/state.md, planning.md, adaptation.md, capacity.md; templates/handoff.md and state.json; state.schema.json; both helper scripts. Sources observed:

- `scripts/planning_state.py` SHA-256 `af80052eeac36ee5f3829b0d6879c6d88f2280f6c06a5dc393dadc3b8b57a1f3`
- `scripts/planning_capacity.py` SHA-256 `397c50e4f2566eb2be4976d8f077913bcfe67d1c17f7eeac686a6d1c2c73ee8a`
- `state.schema.json` SHA-256 `246449edea0cf64ab8ca91cdbdde8c2247a0f2033745d3dc22b63a81b72c3726`

## Finding: P2 — overlapping protection incorrectly invalidates the state

Location: `scripts/planning_state.py`, original line 249, unconditional overlap reporting for the combined fixed/block span list.

Two protected intervals may describe the same unavailable time without contradictory attendance obligations. The capacity contract expressly subtracts their union once. Capacity arithmetic does that correctly, but the checker first marks the state invalid whenever those protections overlap. Therefore the capacity report returns `valid:false` and `feasibility:constraints-invalid`, and commit rejects an otherwise legitimate representation of protected time. This is distinct from two conflicting fixed commitments, which should still surface a conflict, or a work block inside protected time, which should remain an error.

Suggested bounded repair: distinguish protective reservations from attendance/work spans in overlap checking; union overlapping protection while preserving errors for work inside it and conflicting hard attendance. Check sleep-protection nesting too, since an unavailable event during declared sleep is also not inherently a contradictory commitment. Do not simply disable all overlap checks.

Exact synthetic input:

```json
{
  "schema_version": 2,
  "plan_id": "synthetic-plan",
  "revision": 0,
  "updated_at": "2026-11-02T07:00:00-07:00",
  "profile": {
    "timezone": "America/Denver",
    "week_start": 0,
    "sleep": {
      "start": "23:00",
      "end": "07:00"
    }
  },
  "tasks": [
    {
      "id": "work",
      "title": "work",
      "remaining_minutes": 480,
      "deadline": "2026-11-02T14:00:00-07:00",
      "preferred_date": null,
      "priority": "high",
      "required": true,
      "flexible": true,
      "dependencies": [],
      "min_session_minutes": 30,
      "recurrence": null
    }
  ],
  "occurrences": [],
  "fixed_events": [
    {
      "id": "protect1",
      "title": "Protected family time",
      "kind": "protected",
      "start": "2026-11-02T10:00:00-07:00",
      "end": "2026-11-02T12:00:00-07:00"
    },
    {
      "id": "protect2",
      "title": "Protected rest",
      "kind": "protected",
      "start": "2026-11-02T11:00:00-07:00",
      "end": "2026-11-02T13:00:00-07:00"
    }
  ],
  "model_week": [],
  "dated_plan": {
    "start": "2026-11-02",
    "end": "2026-11-03",
    "blocks": [],
    "unscheduled": []
  },
  "progress": [],
  "feedback": [],
  "adaptations": [],
  "applied_updates": [],
  "extensions": {
    "constraints_v2": {
      "availability": [
        {
          "start": "2026-11-02T09:00:00-07:00",
          "end": "2026-11-02T14:00:00-07:00"
        }
      ],
      "buffer_percent": 20
    }
  }
}
```

Invocation: `planning_capacity.capacity(input, '2026-11-02T07:00:00-07:00')` after importing the candidate script without bytecode writes.

Exact output:

```json
{
  "valid": false,
  "errors": [
    "protect1: overlaps protect2"
  ],
  "warnings": [
    "work: 480 minutes unallocated (required)",
    "capacity is an aggregate bound; task capacities share time and do not prove joint placement or readiness"
  ],
  "feasibility": "constraints-invalid",
  "availability_known": true,
  "views": {
    "day": {},
    "week": {},
    "month": {}
  },
  "allocated_minutes": 0,
  "dependency_readiness": {},
  "candidate_minutes": 120,
  "buffer_minutes": 24,
  "buffer_method": "percentage",
  "buffer_percent": 20,
  "usable_minutes": 96,
  "unallocated_usable_minutes": 96,
  "allocated_over_capacity_minutes": 0,
  "required_minutes": 480,
  "shortfall_minutes": 384,
  "tasks": {
    "work": {
      "remaining_minutes": 480,
      "eligible_upper_bound_minutes": 96,
      "shortfall_lower_bound_minutes": 384,
      "minimum_session_minutes": 30,
      "dependency_readiness": "not-applicable"
    }
  },
  "deferred_requirements": [],
  "unresolved_requirements": []
}
```

Expected: protected union10:00–13:00 subtracts180min from300, yielding120 candidate/24buffer/96usable; no constraint-invalid solely because protective reservations overlap. With480 required, the honest arithmetic result is overloaded, shortfall384min.

## Re-probes of parent fixes

- Prior sleep anchor: availability Nov2 09:00–14:00−07:00; exception anchored Oct30 23:00−06:00 through Nov2 10:00−07:00. Observed candidate240, buffer48, usable192; the earlier-starting protected interval is honored. No unresolved duplicate finding.
- Per-task buffer: same300min availability/20%buffer; task60min due10:00. Observed eligible upper bound60, task shortfall0, feasibility not-proven. The aggregate60min buffer can lie later; it is not charged again in the task window. No unresolved duplicate finding.
- Required recurrence inventory: required daily work, count1, minutes30, missing Nov2 occurrence. Observed required_minutes=null, shortfall_minutes=null; unresolved_requirements names work@daily:2026-11-02#1 and reports unknown required effort. No false zero-demand certificate.
- Basic frozen capacity case:480required,300available,20%buffer produces240usable,240shortfall, overloaded.

Capacity is an upper-bound report, not a joint solver. Shared eligible intervals, unverified dependencies, and not-proven feasibility are intentionally not reported as defects. This bounded review does not establish exhaustive correctness or a superiority claim.

## Resolution re-probe after constructor repair

The original finding above is preserved as the observed pre-fix result and is now resolved by independent re-probe. Exact original protection input was rerun unchanged. It now returns valid=true, candidate120, buffer24, usable96 and overloaded/shortfall384, without a protection-overlap error. Two contrasts retain invalidation: changing both protection kinds to fixed reports conflicting fixed meetings; replacing the second protection with planned work1 at11:00–11:30 inside protection10:00–12:00 reports that work overlap.

### overlapping protection

```json
{
  "valid": true,
  "errors": [],
  "warnings": [
    "work: 480 minutes unallocated (required)",
    "capacity is an aggregate bound; task capacities share time and do not prove joint placement or readiness"
  ],
  "feasibility": "overloaded",
  "availability_known": true,
  "views": {
    "day": {},
    "week": {},
    "month": {}
  },
  "allocated_minutes": 0,
  "dependency_readiness": {},
  "candidate_minutes": 120,
  "buffer_minutes": 24,
  "buffer_method": "percentage",
  "buffer_percent": 20,
  "usable_minutes": 96,
  "unallocated_usable_minutes": 96,
  "allocated_over_capacity_minutes": 0,
  "required_minutes": 480,
  "shortfall_minutes": 384,
  "tasks": {
    "work": {
      "remaining_minutes": 480,
      "eligible_upper_bound_minutes": 96,
      "shortfall_lower_bound_minutes": 384,
      "minimum_session_minutes": 30,
      "dependency_readiness": "not-applicable"
    }
  },
  "deferred_requirements": [],
  "unresolved_requirements": []
}
```

### overlapping actual fixed meetings

```json
{
  "valid": false,
  "errors": [
    "protect1: overlaps protect2"
  ],
  "warnings": [
    "work: 480 minutes unallocated (required)",
    "capacity is an aggregate bound; task capacities share time and do not prove joint placement or readiness"
  ],
  "feasibility": "constraints-invalid",
  "availability_known": true,
  "views": {
    "day": {},
    "week": {},
    "month": {}
  },
  "allocated_minutes": 0,
  "dependency_readiness": {},
  "candidate_minutes": 120,
  "buffer_minutes": 24,
  "buffer_method": "percentage",
  "buffer_percent": 20,
  "usable_minutes": 96,
  "unallocated_usable_minutes": 96,
  "allocated_over_capacity_minutes": 0,
  "required_minutes": 480,
  "shortfall_minutes": 384,
  "tasks": {
    "work": {
      "remaining_minutes": 480,
      "eligible_upper_bound_minutes": 96,
      "shortfall_lower_bound_minutes": 384,
      "minimum_session_minutes": 30,
      "dependency_readiness": "not-applicable"
    }
  },
  "deferred_requirements": [],
  "unresolved_requirements": []
}
```

### task inside protection

```json
{
  "valid": false,
  "errors": [
    "protect1: overlaps work1"
  ],
  "warnings": [
    "work: 450.0 minutes unallocated (required)",
    "capacity is an aggregate bound; task capacities share time and do not prove joint placement or readiness"
  ],
  "feasibility": "constraints-invalid",
  "availability_known": true,
  "views": {
    "day": {
      "2026-11-02": {
        "planned_minutes": 30,
        "block_ids": [
          "work1"
        ],
        "occurrence_ids": []
      }
    },
    "week": {
      "2026-11-02": {
        "planned_minutes": 30,
        "block_ids": [
          "work1"
        ],
        "occurrence_ids": []
      }
    },
    "month": {
      "2026-11": {
        "planned_minutes": 30,
        "block_ids": [
          "work1"
        ],
        "occurrence_ids": []
      }
    }
  },
  "allocated_minutes": 30,
  "dependency_readiness": {
    "work": "ready"
  },
  "candidate_minutes": 180,
  "buffer_minutes": 36,
  "buffer_method": "percentage",
  "buffer_percent": 20,
  "usable_minutes": 144,
  "unallocated_usable_minutes": 114,
  "allocated_over_capacity_minutes": 0,
  "required_minutes": 480,
  "shortfall_minutes": 336,
  "tasks": {
    "work": {
      "remaining_minutes": 480,
      "eligible_upper_bound_minutes": 144,
      "shortfall_lower_bound_minutes": 336,
      "minimum_session_minutes": 30,
      "dependency_readiness": "ready"
    }
  },
  "deferred_requirements": [],
  "unresolved_requirements": []
}
```

Reviewed repair snapshot SHA-256: 3e833002c18a6dc636f8824b0cb55a5160699605d3b89a343bdb13d653a74521. No transitive dependency probe was run in this pass; parent indicated that repair was still in progress. No model responses were rerun.
