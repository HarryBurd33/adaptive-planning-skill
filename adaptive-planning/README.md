# Adaptive planning

A self-contained assistant skill for sustainable daily, weekly and monthly planning, model weeks, disruption repair and feedback-based adjustments. Compass is its substantive workflow foundation; no Compass installation is needed.

Invoke with `$adaptive-planning Plan next week around my exams`, or ask naturally: “My meeting displaced lifting; replan from the saved state.” A general question such as “What is productivity?” should not activate this workflow.

Install the entire `adaptive-planning` folder into the user-level `~/.agents/skills/` directory to use it across local Codex projects. You can ask `$skill-installer` to install `HarryBurd33/adaptive-planning-skill`, path `adaptive-planning`, with destination `~/.agents/skills`. The skill should appear on the next turn; restart Codex if discovery does not refresh. Other computers or remote environments need their own installation. The folder's name must remain equal to its metadata name. Obsidian/calendar integration and scheduled check-ins are optional, require actual supported tools and separate authorization.

Use conversation alone, or put personal state in a location you choose **outside** this folder. See [state and continuity](references/state.md) for the JSON contract, portable handoff and optional helper commands. The helper requires Python 3.9+ and IANA timezone data; basic planning has no runtime dependency. Never put real planning records in examples or release archives.

Start with your planning horizon/timezone, hard commitments, protected sleep, tasks and deadlines, recurring activities, and desired free time. Supply updates incrementally. The assistant should ask only for missing facts that affect feasibility and label provisional assumptions. You can undo a routine adaptation by its ID.

See [synthetic scenarios](examples/scenarios.md), [provenance and licensing](references/provenance.md), and [validation results](validation/report.md). Validation distinguishes authored illustrations, executed utility checks, static structure and real model responses; it does not prove long-term personal outcomes.

License: original code/resources are MIT. The Compass-derived `SKILL.md` and `references/planning.md` retain CC BY 4.0. See [NOTICE](NOTICE.md) for exact scope.

Version0.2.0: [explicit capacity and canonical views](references/capacity.md), version2 opt-in constraints, and `--as-of` elapsed-history checks. Version1 state stays readable; no personal migration runs during installation.

Version0.3.0 adds optional read-only trial reporting and local calendar/Markdown exports. See [trial](references/trial.md) and [exports](references/exports.md); live synchronization and reminders remain separate capabilities.
