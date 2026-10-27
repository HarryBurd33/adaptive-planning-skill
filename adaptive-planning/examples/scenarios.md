# Synthetic examples — illustrations, not executed model tests

These are authored demonstrations. Actual model outputs and utility results are separately identified in [the validation report](../validation/report.md). All personal data is synthetic.

## Initial week

Input: “Plan the week beginning 2026-11-02 in America/Denver. Sleep 23:00–07:00. Classes Monday, Wednesday, and Friday 09:00–12:00. A paper needs six hours and is due Friday at 17:00. I want three one-hour lifting sessions, 30 minutes of reading daily, and two hours of laundry on Sunday.”

An illustrative **provisional** allocation follows. Only the supplied sleep/classes/deadline are confirmed. Candidate work windows below assume no other commitments; ask if that assumption changes feasibility. For illustration reserve breakfast08:00–08:30, lunch12:00–13:00 (12:15–13:15 on class days), dinner18:00–19:00, 15 minutes each side of classes/lifting, 90 minutes/day of desired free time, and a further 20% buffer. These are transparent example estimates, not known personal preferences. Protect 23:00–07:00 every day.

| Date | Time | ID | Activity |
| --- | --- | --- | --- |
| Mon Nov 2 | 09:00–12:00 | C-M | Class |
| Mon Nov 2 | 13:15–15:15 | P1 | Paper |
| Mon Nov 2 | 16:00–17:00 | L1 | Lifting |
| Tue Nov 3 | 13:00–15:00 | P2 | Paper |
| Wed Nov 4 | 09:00–12:00 | C-W | Class |
| Wed Nov 4 | 16:00–17:00 | L2 | Lifting |
| Thu Nov 5 | 13:00–15:00 | P3 | Paper |
| Fri Nov 6 | 09:00–12:00 | C-F | Class |
| Fri Nov 6 | 16:00–17:00 | L3 | Lifting |
| Sun Nov 8 | 14:00–16:00 | A1 | Laundry |
| Nov 2, 3, 4, 5, 6, 7, 8 | 20:30–21:00 each | R2…R8 | Reading, one dated occurrence/day |

Capacity under these illustrative assumptions: 6,720 waking minutes − 540 class − 1,050 meals − 180 transitions − 630 desired free time = 4,320 candidate minutes. Buffer864; usable3,456. Allocated flexible work870; usable unallocated2,586. The totals alone do not prove personal availability; all placed sessions must also fit their specific windows. This example leaves ample open time.

| Task | Required | Planned | Unmet |
| --- | --- | --- | --- |
| Paper, due Nov6 17:00 | 360m | 360m by Nov5 15:00 | 0 |
| Lifting | 3×60m | 180m in3 sessions | 0 |
| Reading | 7×30m | 210m in7 daily sessions | 0 |
| Laundry, Sunday | 120m | 120m Nov8 | 0 |

## Disruption and partial progress

At Wed Nov4 13:00, input: “A Wednesday meeting from 16:00–17:30 conflicts with my planned lifting session. Tuesday’s paper session is already completed.”

Mark P2 actually completed, once. It contributes120m of progress, so paper remaining240m unless P1 completion is also reported; P1's elapsed slot must not be assumed complete. If P1 has no progress report, identify the unknown and reallocate its remaining requirement in a future eligible window, with the plan conditional until clarified. Do not recreate P2. Move only L2 from Wed16:00 to Thu16:00 if that window is available; carry its transitions. Leave P3, L1/L3 history and other unaffected future blocks as appropriate. If P1 was completed too, paper remaining120m is already covered by P3. This distinction prevents a plausible-looking plan from inventing completion.

## Feedback and undo

Input: “I skipped evening reading three times because I was exhausted. Morning reading worked twice. Keep my wake time unchanged.”

Record the five reported observations, move future reading to an available07:15–07:45 window, preserve07:00 wake and the prior evening setting. Explain adaptation A-read-morning and its evidence; “undo A-read-morning” restores the prior preference through a new recorded decision. If mornings are unavailable, report it and offer another eligible window. Unknown days are not misses.

## Overload

Input: “Eight hours of required work remain before the deadline, but only four usable hours remain.”

“The shortfall is four hours. Four hours can be scheduled; four remain unmet. Which can change: scope, deadline, or the priority of another movable commitment?” Do not spend protected sleep or claim eight hours fit.

## Month and continuity

A November view includes the whole recurrence period Oct26–Nov2 when showing Nov1. If two of three weekly lifting sessions were completed Oct27/29, one remains; November does not reset the week. A monthly plan shows milestone/capacity commitments, not invented hourly appointments for every future day.

A portable handoff must retain timezone/week boundaries/sleep, task and occurrence IDs, remaining effort, dated future blocks, completed/unknown progress, model week, temporary exam exceptions, feedback/adaptations with undo, revision/update IDs and unresolved assumptions. A fresh chat reads that handoff before planning. With no calendar or scheduler, it returns text and state, without claiming events or reminders were created.
