# Foundation and changes

Inspected [AgriciDaniel/compass](https://github.com/AgriciDaniel/compass) at immutable revision **ba2c1cf73a8e305c02fa8819f0236f028fd972b3**, retrieved 2026-10-26 America/Denver (2026-10-27 UTC). It is an Obsidian vault/template/prompt foundation, not an installed adaptive-planning skill. The following actual files were inspected through the GitHub connector:

| Inspected file | Substantive contribution and change here |
| --- | --- |
| [Guide/05 Workflow - Multi-Scale Planning.md](https://github.com/AgriciDaniel/compass/blob/ba2c1cf73a8e305c02fa8819f0236f028fd972b3/Guide/05%20Workflow%20-%20Multi-Scale%20Planning.md) | Adapted daily/weekly/quarterly parent-scale intentions and review into daily/weekly/**monthly** consistency. Monthly is newly added; no retreat prerequisite. |
| [03 Planning/Ideal Week.md](https://github.com/AgriciDaniel/compass/blob/ba2c1cf73a8e305c02fa8819f0236f028fd972b3/03%20Planning/Ideal%20Week.md) | Retained the model-week versus dated-schedule distinction. Removed example personal routines and mandatory daily questions. |
| [Templates/Daily Note.md](https://github.com/AgriciDaniel/compass/blob/ba2c1cf73a8e305c02fa8819f0236f028fd972b3/Templates/Daily%20Note.md) | Adapted daily/weekly intention and task links into concise dated agendas, progress and optional reflection. Removed vault queries and Templater dependencies. |
| [Templates/Weekly Note.md](https://github.com/AgriciDaniel/compass/blob/ba2c1cf73a8e305c02fa8819f0236f028fd972b3/Templates/Weekly%20Note.md) | Adapted priorities, model-week check and review into capacity/recurrence checks. No fixed number of intentions. |
| [Prompts/01 Morning Start.md](https://github.com/AgriciDaniel/compass/blob/ba2c1cf73a8e305c02fa8819f0236f028fd972b3/Prompts/01%20Morning%20Start.md) | Retained read-current-sources-before-planning; replaced Obsidian operations with optional state access and conversational fallback. |
| [Prompts/02 End of Day Coaching.md](https://github.com/AgriciDaniel/compass/blob/ba2c1cf73a8e305c02fa8819f0236f028fd972b3/Prompts/02%20End%20of%20Day%20Coaching.md) | Adapted reflection in the person's words without assigning scores into factual, optional check-ins. |
| [Prompts/03 Weekly Review.md](https://github.com/AgriciDaniel/compass/blob/ba2c1cf73a8e305c02fa8819f0236f028fd972b3/Prompts/03%20Weekly%20Review.md) | Retained missing-data-versus-failure and repeated-theme evidence distinctions; added reversible adaptation records. Three observations is a proposed guardrail, not a validated universal threshold. |
| [Prompts/06 Task Triage.md](https://github.com/AgriciDaniel/compass/blob/ba2c1cf73a8e305c02fa8819f0236f028fd972b3/Prompts/06%20Task%20Triage.md) | Retained real-deadline discipline, source preservation and visible changes; removed vault tags and project/person conventions. |

New original mechanisms: explicit usable-capacity/shortfall arithmetic, buffering, effort/dependency/session checks, monthly overviews, full-period recurrence identifiers, partial-progress/idempotency handling, minimal-change repair, evidence-linked reversible adjustments, revision-controlled state and portable continuity. This package is not a full scheduling optimizer or a separate application.

## Reuse rights and attribution

The [root LICENSE](https://github.com/AgriciDaniel/compass/blob/ba2c1cf73a8e305c02fa8819f0236f028fd972b3/LICENSE), [LICENSE-GUIDE.md](https://github.com/AgriciDaniel/compass/blob/ba2c1cf73a8e305c02fa8819f0236f028fd972b3/LICENSE-GUIDE.md), [THIRD_PARTY_NOTICES.md](https://github.com/AgriciDaniel/compass/blob/ba2c1cf73a8e305c02fa8819f0236f028fd972b3/THIRD_PARTY_NOTICES.md), and [CREDITS.md](https://github.com/AgriciDaniel/compass/blob/ba2c1cf73a8e305c02fa8819f0236f028fd972b3/CREDITS.md) were read. Templates/prompts are MIT; Guide prose is CC BY 4.0; plugin binaries have separate terms including copyleft licenses. No plugin code, binary, assets or configuration are bundled or required.

Credit: **the Compass vault template authors**, AgriciDaniel/compass, revision above. The multi-scale workflow in `SKILL.md` and `references/planning.md` is adapted from the Guide; changes are listed above. Those two instructional files are distributed under [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/). Retain this credit, source, license link and indication of changes when redistributing them. Other original files use the package MIT license; this does not relicense upstream material. The full applicable [Compass MIT notice](../licenses/Compass-MIT.txt) and [Guide license notice](../licenses/Compass-LICENSE-GUIDE.md) are retained.

Compass credits Cal Newport for multi-scale planning, Mike Schmitz's public Practical PKM video for inspiration, and Marshall Goldsmith/Mark Reiter for daily questions. Their underlying works were not inspected or copied. No endorsement is claimed.

## Bounded foundation search

Skill Finder used the connected GitHub reader and targeted primary web search. Query: `site:github.com adaptive planning agent skill schedule feedback deadlines SKILL.md`. One additional candidate, `magnus919/agent-skills/technical-project-management/SKILL.md`, was read (blob `21e77a8e65ab7e25db16935ff94e8b8b3e73bb74`). It targets team delivery; its root license returned 404 and immutable commit was not verified. Rejected for reuse; nothing copied. Hugging Face was skipped because no model, dataset or hosted Space was needed. This was a bounded fit review, not an exhaustive search. No downloaded code was executed.

Version0.2.0 (2026-10-30) adds original capacity/state checking code, version2 opt-in constraints, as-of preservation, and concise handoff guidance. Guide-derived SKILL.md/planning prose remains CC BY4.0 with the same attribution; original code/resources remain MIT. No additional Compass files or plugins were imported.

Version0.3.0 adds original stdlib trial reporting and portable export code/resources. iCalendar behavior is implemented from the RFC5545 format contract; no RFC code or external implementation is copied. The optional developer-only icalendar parser is installed from a pinned requirement, not bundled. Personal trial data is excluded. Existing Compass attribution and CC BY4.0 instructional-file exceptions remain unchanged.
