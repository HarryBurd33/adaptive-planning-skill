# Capacity and multi-scale planning

The relationship between daily and weekly intentions, review, and a distinct ideal/model week is adapted from the Compass Guide and templates. Monthly planning, arithmetic and recurrence rules below are additions. See [provenance](provenance.md) and the CC BY 4.0 notice there.

## Capacity is a budget

Use local dates in the profile timezone and actual elapsed minutes for dated blocks. A block is half-open `[start,end)`: touching endpoints do not overlap. Validate timestamp offsets against the IANA zone; crossing midnight and DST may change elapsed duration. Ask about nonexistent or repeated local times rather than guessing. A week starts on the stored local weekday, not every month’s first day.

For each deadline or recurrence period, calculate:

`candidate time = confirmed available intervals (or labeled provisional windows) minus union(sleep, fixed events, protected time, meals/breaks/transitions, desired unscheduled time)`

`usable capacity = candidate minutes minus stated buffer minutes`

`shortfall = max(0, required remaining minutes minus usable eligible minutes)`

Compute eligibility per task too: a six-hour opening is not usable for a prerequisite-dependent task if its prerequisite cannot be completed in time. A 15-minute gap cannot fit a 30-minute minimum session. Count overlaps once. Use actual available windows rather than a weekly grand total to justify deadline feasibility. Do not turn an unknown estimate into a precise promise. Offer a provisional range or ask if it changes the choice.

Default buffer is a visible proposal of 20% of candidate time, rounded conservatively to whole minutes. It is not a universal recommendation about personal capacity. A user's requested free afternoon is protected independently of that buffer. Do not reserve buffer twice under multiple names. Show how much remains unscheduled; the goal is sufficient capacity with recovery time.

## Place work without inventing it

Keep task IDs through moves, renames and partial progress. For required deadline tasks, allocate the full known remaining effort before the deadline and identify milestones. If an effort estimate is uncertain, label the plan conditional. Record session size and relevant setup/travel/recovery time. Avoid splitting below the minimum useful duration unless the user changes it.

For a recurrence, separate the series from occurrences. Each occurrence has a full local period and target; a weekly series has one quota for that week even if the month changes. Example: the Monday-start week `2026-10-26` through (exclusive) `2026-11-02` belongs to one weekly period. Oct 31 and Nov 1 views must refer to that same period, not create a fresh November quota. Use a stable period anchor and sequence in IDs. Daily missed reading does not automatically become tomorrow's extra reading. If the user wants catch-up, make that a new explicit decision.

Daily and weekly recurrence means the user's stated frequency, not a guessed interval. Clarify or expose provisional handling of ambiguous “three times a month,” minimum spacing, or preferred days when it matters. A monthly deadline on a nonexistent day requires a visible policy or clarification; never silently roll it into another month. For a partial horizon, distinguish the full-period target, already completed work outside the view, and work allocated inside it.

## Derive views

- Model week: a reusable weekday/window pattern, independent of actual dates. Store explicit durable preference changes here only when evidence supports them. Leave dated exam/holiday exceptions in dated state.
- Month: deadlines and milestones, estimated weekly capacity and recurring commitments. Label uncertain weeks. Drill down only where the user needs detail.
- Week: dated work blocks, fixed commitments, recurring allocations, buffer and unmet totals. Carry progress from preceding days and cross-month occurrence IDs.
- Day: select today's canonical blocks plus actual progress and remaining work. A daily completion must update the same task/occurrence used by the weekly and monthly view.

Before showing a view, reconcile totals with the canonical dated plan and progress ledger. Monthly milestones must not promise work that the weekly/day allocations cannot support. Future capacity may be provisional; say what would invalidate the plan.

## Minimal useful questions

Ask about a missing deadline time when Friday morning versus Friday night changes the answer. Ask which overlapping hard event can change. Ask for a scope/deadline/priority decision when required work exceeds usable capacity. Otherwise continue with visible, reversible estimates. Do not ask for an entire personal profile before helping with one displaced session.

With explicit version2 availability, use [the capacity utility](capacity.md) to audit arithmetic and derive canonical views. Its task capacities are shared upper bounds, not independent slots or proof of a jointly feasible placement.
