# Model execution notes

- Phase 1 executed five input cases: initial, overload, feedback, ambiguity, nonactivation, in that order.
- Source read: `.forge/execution-inputs.json` only. Candidate files and frozen expected-result rubric were not opened by this agent during Phase 1.
- Context limitation: this agent inherited full parent history, which includes candidate `SKILL.md` and reference contents already written in tool calls. The baseline is therefore contaminated and cannot establish a clean causal comparison.
- All five responses were generated in the same executor context. Feedback was interpreted against the initial response's reading window. Other cases are separate probes.
- The actual inherited model ID and effort are unavailable to this agent; both are recorded as unknown. No model override was requested.
- Outputs are actual model-produced responses. They have not been graded here. No real user planning state, calendar events, account connection or background run was created.
- Phase 2 executed after loading candidate core and planning/adaptation/state references: same five inputs plus tool-fallback, fixed-conflict and month-boundary, then staged disruption against the initial candidate response. Outputs saved in `candidate-responses.md` before reading the frozen expected-result rubric.
- Independent resource inspection is saved in `resource-review.md`; temporary helper probes found an invalid model-week shape accepted silently and historical missed recurrence reported as unallocated work. Candidate files were not edited.
- Fresh-context continuity remains a separate parent-owned execution because this executor context is not fresh.
