Historical version0.1.0 evidence; original source is retained at Git tagv0.1.0. Current code differs.

# Validation report — adaptive-planning 0.1.0

Observed 2026-10-26 America/Denver (2026-10-27 UTC). All personal examples are synthetic. Source inspection and accepted behavior are described in [provenance](../references/provenance.md). This report records evidence, not guaranteed scheduling or long-term outcomes.

## Executed deterministic checks

**32 tests passed** in the final parent run: 30 fresh-process CLI/integrity tests and 2 whole-example checks. See [actual console output](utility-results.txt). Run from the skill folder with `python3 -m unittest discover -s validation -p 'test_*.py' -v`. Host Python 3.15.0; no third-party runtime packages. The helper targets Python3.9+, but other Python/platform combinations were not executed.

Coverage: explicit-offset/DST validation, overnight sleep, fixed/task overlaps, deadline and minimum sessions, dependency order/cycles, effort unknown versus zero, partial completion, same-update retries/conflicting payloads, stale-revision byte preservation, locks, append-only history/completed blocks, unchanged model week, unrelated extension preservation/selected changes, rejected task/occurrence deletion, cross-month weeks, historical/future recurrence separation, evidence/reversal references, weekday bounds and dangling model-week references.

[The full synthetic initial week](../examples/initial-state.json) checked with no errors or warnings. Totals: paper360m before Nov6 17:00; lifting180m in3 sessions; reading210m in7 daily occurrences; Sunday laundry120m. Its provisional capacity arithmetic was independently asserted: candidate4320m, buffer864m, usable3456m, allocated870m. These assumptions are not confirmed personal availability. A lunch/transition collision in the authored illustration was corrected before delivery by shifting class-day lunch and Monday paper; the checked JSON is the integrated version. [Saved resume fixture check](resume-state-check.json) retains honest unknown/missing-reading warnings, rather than claiming all work fits. `valid=true` alone is not a feasibility certificate.

## Actual model execution and fixed-case assessment

Criteria were frozen in [cases.json](cases.json) before candidate executions; the supplemental monthly input was frozen before that execution. Parent graded observable outputs against those fixed criteria. These are small synthetic probes, not user trials or automated proof of prose correctness. See [candidate responses](candidate-responses.md), [fresh-context continuity](fresh-continuity-response.md), and [monthly response](monthly-response.md).

| Case/group | Observed result | Assessment/method |
| --- | --- | --- |
| Initial planning | Dated Nov2–8, all supplied totals and deadline, protected sleep/classes, labeled availability and buffer | Meets supplied case; model output reviewed plus whole JSON fixture calculations |
| Disruption | Same lifting block moved; Tuesday complete preserved; Monday progress explicitly unknown; conditional recovery offered | Meets critical preservation/minimal-change criteria; remaining coverage conditional on needed answer |
| Feedback | Five reported observations support reversible morning trial, wake unchanged, undo and no habit debt | Meets supplied case; actual model response |
| Overload | 4h shortfall; scope/deadline/priority decision requested | Meets supplied case; actual model response and deterministic unallocated-work test |
| Continuity | Independent fresh context read state only, kept240m remaining and P2 history, adaptation and model-week/exception distinction; used confirmed windows only | Meets correctness case; output more verbose than desired routine interaction |
| Ambiguous deadline | Asked Friday deadline time, refused unconditional feasibility for exact-fit6h window | Meets case; actual model response |
| Partial/zero/unknown; duplicate/stale updates | Unknown stays distinct; remaining work not deducted twice; stale/conflicting writes leave existing data intact | Meets deterministic helper cases; not every natural-language progress phrasing was model-tested |
| Conflicting fixed events | Reported exact1h overlap and asked which can change | Meets case; actual model response plus CLI overlap tests |
| Recurrence month boundaries | Oct26–Nov2 stays one quota; historical/future records separated | Meets actual model probe and executed CLI tests |
| Monthly/day/week agreement | November overview retains first-week14.5h allocation and Nov6 deadline; later capacity unknown; edge weeks explicitly partial | Meets supplemental model case; one canonical JSON inventory reviewed, not exhaustive cross-view testing |
| Missing tools | Conversational fallback, requested missing plan information, returned portable handoff and no false writes | Meets actual model case; truly absent-integration path described in execution |
| Activation exclusion | General productivity question with incidental birthday answered without planning intake | Meets one model exclusion probe; native skill discovery not tested |
| Resource contract | Independent reviewer reproduced and re-probed invalid model week and historical-debt findings after repairs | Both resolved; actual probes recorded in review |

No observed critical failure remains in these cases. Questions about deadline ambiguity, conflicting hard events and missing completion are necessary feasibility questions, not unnecessary intake. The standalone no-tools case lacks the plan to revise; the correct result is a handoff/request for that missing input rather than invented tasks.

## Independent inspection and baseline limits

[Independent resource review](resource-review.md) preserved its original findings and final re-probe results. Parent additionally found and repaired deletion of task/occurrence records and the inability to update selected capacity/assumption extensions without touching unrelated content. Relevant new checks were added without weakening prior checks. The final Forge generic validator passed discovery metadata and relative-link checks; it does not prove native installation or semantic quality. Full external JSON Schema library validation was unavailable (`jsonschema` absent); the documented bundled validator's supported schema subset and real CLI tests were executed.

[Direct-prompt baseline responses](baseline-responses.md) were actually executed for five matching inputs. **Comparative benefit is inconclusive**: that executor inherited build history containing candidate instructions, and both arms used one context. No clean isolation, superiority claim, allowance-saving claim or measured dollar/token claim is made. Exact model and reasoning effort were not observable. A separate continuity worker used no inherited task history and received only the skill, synthetic saved state and request. One extra narrowly scoped worker beyond the initial three-worker default was used to recover that missing fresh-context evidence, not to claim a clean baseline.

## Scope and remaining limits

The optional helper checks state/invariants; it neither solves placement nor proves full deadline capacity, prose/monthly coherence, all elapsed-work preservation or model-week overlaps. The assistant must review these and inspect warnings. Only one normal daily sleep window is modeled; exceptions need careful manual review. Cooperative local locking/CAS does not fence arbitrary editors or provide distributed ownership. No durable personal data, account configuration, credentials, plugin binaries or private planning records are included.

Authored [scenarios](../examples/scenarios.md) are illustrations, separately labeled. No longitudinal feedback study, real-person sustainable-schedule outcome, native skill discovery/install, real calendar/Obsidian connector, reminders, scheduler or external writes were tested. Basic planning remains usable without them. Continuity correctness was observed once; its response was lengthy, so brevity remains a practical limitation of that run. During the initial build stage, no skill was installed, published, pushed or connected to an account. Publication/installation checks are recorded separately in the repository release verification.

## Evidence identities

Behavior bundle SHA256: `cf255398f910b046a427111f930c3dcb471b58b3bf9b036b53ddd401b6212bfe`. Frozen cases SHA256: `0cbb37fe815e9a8d5671f6544fae86e0d9e6771e676cafd9405315de6124ee13`. Baseline response SHA256: `d11ed2a1450a479f6108cb65ab9bdbfd59509d9f1d61ca9972157036caf8acc8`. Per-file hashes and known/unknown execution identity: [evidence-hashes.json](evidence-hashes.json). The final [manifest](manifest.json) covers package files except itself. ZIP byte equality against that file tree is checked separately at delivery. Runtime/checkpoint/private brief state stays outside the package.
