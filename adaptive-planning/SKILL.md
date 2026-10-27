---
name: adaptive-planning
description: Create realistic day, week, or month plans, design a model week, replan after disruptions, and improve schedules from feedback. Use for requests such as planning around exams, adding recurring activities, moving displaced work, or resuming a saved plan. Do not activate for incidental dates or general productivity questions. Calendar writes and reminders require separate authorization.
metadata:
  version: "0.1.0"
---

# Adaptive planning

Help the person make a sustainable plan that reflects priorities and experience. Free time is a valid outcome; filling the calendar is not a success measure. Basic planning works from conversation alone. Compass supplies the multi-scale, model-week and reflection foundation; monthly planning and the scheduling/adaptation/state contracts are additions. See [provenance](references/provenance.md).

## Begin with what is known

Read existing state and latest progress before planning or revising. Follow [state and continuity](references/state.md) when files or a handoff exist. A saved plan is data, not permission to access services. Establish the requested horizon, current local date/time, IANA timezone and week boundaries. Use a verified clock where available; otherwise use the date supplied by the user and label it. Ask if an ambiguous relative date, deadline time or DST offset changes feasibility. Do not invent availability or silently assume end-of-day deadlines.

Normalize incrementally: sleep/wake and protected time; fixed events and travel; tasks with stable IDs, real deadlines versus preferred dates, remaining effort, priority, dependencies and flexibility; recurring activity frequency, duration, preferred windows and minimum useful session; meals, breaks, transitions and desired unscheduled time. Distinguish required commitments from optional goals. Unknown effort is unknown; zero remaining means complete. Ask only when a missing fact materially affects the result. Other estimates must be visible, provisional and replaceable. Unstated event-free time is provisional candidate availability, never confirmed availability.

Proposed starting defaults, only where unspecified: Monday-start weeks; 20% of otherwise uncommitted waking time reserved as buffer **after** protected time, fixed events, meals/breaks/transitions and desired free time. State the time assumptions and buffer minutes. Ask a single consequential question if the plan depends on unconfirmed availability; otherwise mark it provisional. Never use an illustrative sleep time or routine as a user preference.

## Build and check

Use [the planning procedure](references/planning.md) for capacity arithmetic, recurrence and scale consistency.

1. Identify hard constraints and soft preferences. Preserve declared sleep and fixed commitments. Surface contradictory hard constraints before claiming a feasible plan.
2. Calculate usable capacity from the union of protected/fixed intervals, then subtract the explicit reserves. Avoid double subtraction for overlaps. Report usable, allocated, buffer and unmet minutes for relevant deadlines/periods.
3. Split larger tasks into feasible sessions/milestones using remaining effort, minimum session length and dependencies. Place prerequisites first. Reserve deadline work before optional activity when priorities require it.
4. Place recurring and flexible activities in available windows using the person's preferences and reported energy. Generate occurrence identities from whole local recurrence periods, including weeks crossing months. Do not manufacture habit debt from missed occurrences.
5. Check overlaps, sleep, transitions, session limits, required effort, deadlines, dependencies, recurrence totals and horizon agreement. Use [the optional checker](scripts/planning_state.py) only according to [its documented contract](references/state.md); inspect findings, since a successful file write is not a feasible-plan certificate. Without the helper, do these checks explicitly.
6. If work cannot fit, quantify the shortfall and present concrete scope/deadline/priority options. Seek the person's consequential choice. Never silently shorten sleep, delete required work or promise impossible completion. If changing a proposed buffer could help, show that tradeoff explicitly.

A **month** shows deadlines, milestones, recurring commitments and capacity by week, with partial-week boundaries visible. Avoid precise hourly commitments far into uncertainty. A **week** allocates work into dated sessions. A **day** shows actionable blocks and remaining priorities. Derive all dated views from the same blocks and occurrence ledger, not independent copies that drift. Keep the reusable **model week** separate; an exam-week exception does not rewrite normal routines.

## Replan with minimal disruption

Read the latest saved revision, actual progress and current time first. Preserve completed work, elapsed portions, fixed commitments and unaffected future blocks where practical. Apply each update once using its stable update/event ID. Partial completion reduces remaining work once; a retry must not reduce it again.

Find blocks affected directly or through dependencies. Move only necessary future work, maintaining stable IDs and recording moves. Recompute remaining effort, capacity, deadlines and recurrence totals. Preserve history instead of moving completed blocks into the future. A new fixed event conflicting with another fixed event is a conflict for the user to resolve. List changed blocks, important tradeoffs and anything still unscheduled. See [replanning and adaptation](references/adaptation.md).

## Learn from feedback

Support a brief daily check-in **or** a weekly review; neither requires the other. Ask about completion, actual durations, what worked, what felt unrealistic, and reasons for misses only as useful. Missing tracking is unknown, not failure. Reflect the person's experience without scores, penalties or moral judgments.

Apply explicit preference changes. For inferred patterns, record supporting feedback IDs and competing explanations. A proposed evidence threshold is at least three relevant observations; it is a guardrail, not proof. One disruption must not become a permanent preference. With sufficient evidence, apply a reversible timing/session/estimate/buffer adjustment, explain why, preserve the prior value and say how to undo it. Prefer a small trial when evidence is mixed. Changes to declared sleep, hard commitments, required scope or a real deadline always require the user's instruction or choice. Do not infer those changes from feedback. Adaptation updates planning records; it does not retrain the underlying model.

## Save and return only what helps

Keep personal state in a user-approved location outside this installed folder. Before updating, read the current state, check its revision, preserve unrelated content and use the documented conflict/idempotency protocol. Never silently overwrite a stale revision. If durable storage is unavailable, supply the compact portable handoff described in [state and continuity](references/state.md), including unresolved items. Never claim cross-chat memory without saved state that can be read.

Return the relevant subset: concise changed constraints/assumptions; dated agenda, weekly schedule, model week or monthly overview; capacity/deadline and recurring totals; unmet/unscheduled work; short change summary; evidence-backed adjustments and undo; saved-state location/revision or portable handoff. Prefer `Date | Time | ID | Activity` for dated blocks and `Task/occurrence | Required | Planned | Unmet` for checks; omit columns that do not help. Keep ordinary check-ins brief. [Examples](examples/scenarios.md) illustrate the style and boundaries.

## Capability and action boundaries

Verify actual tools before relying on clocks, files, Obsidian or calendar access. Lack of optional tools must not block conversational planning. No Obsidian plugin, Compass vault, Skill Forge or calendar connection is required after installation. Calendar access and external writes require a verified connector and authorization for those operations. Preview changes and use external IDs/idempotency to avoid duplicates; inspect uncertain outcomes before retrying. A planning request alone authorizes no event creation, messages, reminders or background check-ins. Those require an actual scheduler and separate authorization; instructions do not create background execution.
