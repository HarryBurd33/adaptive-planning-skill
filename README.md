# Adaptive Planning for Codex

Turn deadlines, fixed commitments, recurring activities, sleep preferences and feedback into realistic daily, weekly and monthly plans. Keep free time, surface overload and repair disruptions without discarding completed work. The skill uses Compass as a substantive planning/review foundation and adds monthly planning, capacity checks, reversible adaptations and optional durable state.

## Install globally for local Codex chats

In Codex, ask:

```text
Use $skill-installer to install the skill from HarryBurd33/adaptive-planning-skill,
path adaptive-planning, into ~/.agents/skills.
```

Or clone this repository and copy its `adaptive-planning` folder to `~/.agents/skills/adaptive-planning`, preserving every supporting file. Stop if that destination already exists; compare your existing copy before updating it. This is a user-level installation for local projects on that computer. Other computers, cloud tasks and remote hosts need their own copy. Codex detects new skills automatically; use it on your next turn, or restart Codex if it has not appeared. See the [official skill documentation](https://learn.chatgpt.com/docs/build-skills).

## Use it

Start a chat with `$adaptive-planning`, followed by your request. For example:

```text
$adaptive-planning Plan next week in America/Denver. Protect sleep 23:00–07:00.
I have classes Monday, Wednesday and Friday 09:00–12:00. My paper needs six
hours and is due Friday at 17:00. Include three one-hour lifting sessions,
30 minutes of reading each day and two hours of laundry on Sunday.
```

Then give short updates:

- “Wednesday's 16:00–17:30 meeting displaced lifting. Tuesday's paper work is complete.”
- “Evening reading failed three times because I was tired; mornings worked twice. Keep wake time unchanged.”
- “Show a monthly overview, keeping later weeks provisional.”
- “Undo adaptation A-reading-morning.”

For continuity, choose a private state location **outside this repository and installed skill**, then say: “Save my planning state to this path.” In another chat, provide that path and ask the skill to read it before replanning. Without file access, request a portable handoff and paste it into the next chat. It does not create cross-chat memory without accessible saved state.

## What is implemented and checked

| Capability | Implementation/evidence |
| --- | --- |
| Day/week/month plans and model week | Assistant workflow; executed synthetic planning/monthly cases |
| Capacity, deadlines, recurrence, overload | Explicit arithmetic, full-period occurrence IDs; scheduling fixtures and model probes |
| Replanning and feedback | Preserve confirmed progress, repair affected future work, evidence-linked reversible adjustments; staged model cases |
| Local state and portable continuity | Documented JSON schema; CAS/idempotent atomic helper; fresh-context synthetic resume |
| Optional integrity checker | Python standard library; 32 executed tests covering constraints, DST, state conflicts and whole examples |

The skill provides instructions for a capable assistant; it is not an autonomous scheduling application or a full optimizer. The helper does not prove all capacity, adaptation quality or prose-view consistency. Read its warnings and the [validation report](adaptive-planning/validation/report.md), including the inconclusive baseline comparison. Long-term personal outcomes are untested.

Conversation-based planning needs no Compass vault, Obsidian, calendar, Python or Skill Forge installation. The optional helper needs Python 3.9+ and IANA timezone data. Calendar/Obsidian operations require an actual supported connector and authorization. Reminders/background check-ins require a real scheduler and separate authorization; they are not included features.

## Run the checks

```sh
python3 -m unittest discover -s adaptive-planning/validation -p 'test_*.py' -v
python3 scripts/validate_release.py
python3 adaptive-planning/scripts/planning_state.py check adaptive-planning/examples/initial-state.json
```

Tests use synthetic data only. The CI workflow runs the deterministic suite and package integrity checks. Model-response examples are recorded evidence, not a guarantee that every assistant will behave identically.

## License and attribution

[MIT](LICENSE) covers original code/resources. The Compass-derived `adaptive-planning/SKILL.md` and `adaptive-planning/references/planning.md` retain **CC BY 4.0**, with required attribution and notices. This is a mixed-license repository; see [NOTICE](NOTICE.md) and [full provenance](adaptive-planning/references/provenance.md). No Compass plugins are bundled.
