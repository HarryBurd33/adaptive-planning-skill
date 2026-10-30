# Portable calendar and Obsidian exports

The optional stdlib helper creates local artifacts from a saved plan. It does not connect accounts, import events, invite attendees, schedule reminders, synchronize files or modify the source state. Live operations still require a verified connector and the user's authorization for the exact operations. A local artifact may contain private task titles and IDs: keep it outside the public repository and installed skill.

```sh
python3 /path/to/adaptive-planning/scripts/planning_export.py /private/planning/state.json --format ics --as-of 2026-11-02T07:00:00-07:00 --output /private/planning/proposed-plan.ics
python3 /path/to/adaptive-planning/scripts/planning_export.py /private/planning/state.json --format markdown --as-of 2026-11-02T07:00:00-07:00 --output /private/planning/proposed-plan.md
```

Without `--output`, exact UTF-8 content goes to stdout. With it, a new file is created with private permissions. An existing regular file succeeds only when its bytes already match; a changed file is preserved and the command fails. Choose a new revision/date filename for a changed export. Symlinks, nonregular files and source-state aliases are refused. Failures exit2 with stderr diagnostics. The destination directory must already exist. This is cooperative local output, not distributed ownership; reconcile concurrent writers first.

The helper validates the whole state with an explicit aware `--as-of`. Errors prevent export. Warnings can remain: a successful export does not certify feasibility or complete availability. Both formats include planned canonical blocks whose end is after as-of, preserving an in-progress block's original start. Completed and ended slots are excluded. Existing fixed appointments are omitted, so this is a proposed work agenda rather than a complete calendar copy.

## Calendar file

The iCalendar subset follows [RFC5545](https://www.rfc-editor.org/rfc/rfc5545): UTC DTSTART/DTEND, UID/DTSTAMP/SEQUENCE and escaped text, CRLF and UTF-8-aware folding. UID hashes plan ID and block ID, remaining stable when the same block moves; another plan has different IDs. DTSTAMP comes from state.updated_at and SEQUENCE from revision, so identical state/as-of exports repeat deterministically. Calendar timestamps use second precision. Unsupported control characters are rejected. No attendees, organizer, method, alarms or invitations are generated. Each event description explicitly identifies a proposed plan and its canonical IDs.

Preview the file before a user chooses to import it. Clients differ in whether reimporting matching UIDs updates existing events or creates duplicates; stable IDs are not a delivery or duplicate-suppression guarantee for arbitrary calendar clients. Removed/completed blocks disappear from this export but do not delete earlier imports. Reconcile old imports explicitly, preferably in a dedicated planning calendar, rather than blindly reimporting. Live bidirectional reconciliation is not implemented.

## Obsidian/Markdown file

The Markdown has plan/revision/timezone/as-of metadata, `Date | Time | ID | Activity`, remaining/future/unmet minutes, unscheduled reasons and checker warnings. User punctuation is entity-encoded so titles cannot break tables or turn into Obsidian embeds/links. It is a standalone note usable without Obsidian plugins. Choose a user-approved vault path or manually move the preview into a vault; the skill does not discover vaults or overwrite existing notes. It is a snapshot, not two-way vault synchronization.

## Optional live services

Discover actual calendar tools before promising them; a listed plugin is not a connected account. For live reads/writes, first identify a connected calendar and exact target, then use connector-specific IDs and the state revision. Keep a private operation ledger with stable local/external IDs, preview the concrete changes, and perform only authorized operations. Inspect an uncertain create/update before retrying; no blind duplicate writes. Do not claim the file export tests verify a live provider. A reminder additionally needs explicit timing/timezone and an actual scheduler with observed delivery. No background jobs are created by installation or export.
