# Release verification

Verified for initial public release on 2026-10-26 America/Denver.

- Public repository: https://github.com/HarryBurd33/adaptive-planning-skill . Root license is detected by GitHub as MIT; NOTICE and README disclose the required CC BY4.0 instructional-file exceptions.
- Initial published skill commit: `7e13207e77d670cc0b047db8001c23689dc9ee3d`.
- All32 deterministic tests passed locally on the reviewed public export and on the installed global copy. The package integrity/metadata/link script passed. Model planning/monthly/replanning/feedback and fresh-context continuity evidence is in the skill validation report; its stated limitations remain applicable.
- GitHub Actions completed successfully on Python3.9 and3.13: https://github.com/HarryBurd33/adaptive-planning-skill/actions/runs/40453074295 . These tests cover the helper and synthetic fixtures, not every possible assistant output or personal outcome.
- The standard Skill Installer installed the exact published commit into the user-level `~/.agents/skills/adaptive-planning` folder. All31 installed file hashes matched the reviewed repository skill tree. No existing skill was overwritten.
- Native Codex app-server `skills/list` with forceReload returned exactly one `adaptive-planning` entry, `scope:user`, `enabled:true`, and no skill errors from both a scratch directory and the build repository. The probe did not start a model turn or change Codex settings. This verifies local user-scope discovery, not automatic installation on other computers/cloud hosts.
- Topics verified: adaptive-planning, agent-skills, codex, codex-skills, compass, obsidian, productivity, python, scheduling, time-management.

This verification adds documentation only; the installed skill tree is unchanged from the initial published commit. Calendar/Obsidian integration and background reminders are not built-in promises. See adaptive-planning/validation/report.md for unsupported checks and the inconclusive baseline comparison.

## Version 0.2.0 verification

The update retains all 32 original tests and passes 70 deterministic cases. Independent full-schema checks validate four fixtures and reject malformed times. Separate fresh baseline/candidate contexts and independent resource review are recorded in adaptive-planning/validation/report.md. The release package is generated reproducibly with scripts/package_skill.py and verified byte-for-byte against the skill folder. Installation must compare the existing unmodified global copy with the preserved baseline and retain rollback. Personal planning state is never migrated during installation. Native discovery and remote CI/readback are recorded at final delivery; do not infer them from this source description alone.
