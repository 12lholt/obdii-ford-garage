# Team Skills

Project-level [Claude Code Skills](https://docs.claude.com/en/docs/claude-code/skills)
live here so they travel with the repo — every collaborator who clones
`obdii-ford-garage` gets them automatically.

## Adding a skill

Create one directory per skill, each containing a `SKILL.md`:

```
.claude/skills/
  <skill-name>/
    SKILL.md        # required: frontmatter (name, description) + instructions
    ...             # optional supporting scripts/files the skill references
```

Minimal `SKILL.md`:

```markdown
---
name: decode-snapshot
description: Summarize an obd_snapshots/*.json capture — connection status, captured signals, and any trouble codes.
---

Steps the skill should follow...
```

Invoke a skill in a session with `/<skill-name>`.

## Ideas for this project
- `decode-snapshot` — turn a raw snapshot JSON into a human-readable health report.
- `add-vehicle` — scaffold a new `vehicles/<slug>.toml` from `vehicles/example.toml`.
- `triage-dtc` — look up a diagnostic trouble code and suggest next steps.

> Note: `.claude/settings.json` (shared) is committed; `.claude/settings.local.json`
> (your personal settings) is gitignored.
