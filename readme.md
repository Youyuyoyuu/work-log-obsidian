# Worklog

`worklog` is a Codex skill for writing the current Codex chat into an Obsidian work log, then restoring project or task memory from those logs later.

It is designed for users who keep project notes in Obsidian and want a repeatable way to preserve decisions, completed work, commands, blockers, and next steps.

## Install

Place this skill folder in your Codex skills directory:

```bash
~/.codex/skills/worklog
```

The folder must contain:

```text
worklog/
├── SKILL.md
├── readme.md
├── config.example.json
├── agents/
│   └── openai.yaml
└── scripts/
    └── worklog_io.py
```

If you are testing a packaging copy on a machine that already has another skill named `worklog`, validate this copy by directory path instead of invoking `$worklog`.

## Configure

Copy the example config and fill in your own Obsidian paths:

```bash
cp config.example.json config.json
```

Example:

```json
{
  "vault_path": "/absolute/path/to/your/ObsidianVault",
  "template_path": "Templates/Daily.md",
  "worklog_folder": "Worklogs",
  "timezone": "local",
  "language": "auto",
  "base_tags": [
    "codex/worklog"
  ]
}
```

Fields:

- `vault_path`: absolute path to the Obsidian vault root.
- `template_path`: daily template path relative to the vault root.
- `worklog_folder`: destination folder for generated work logs, relative to the vault root.
- `timezone`: `local` for the system time zone, or an IANA time zone such as `America/New_York`.
- `language`: `auto` follows the user request or current conversation language.
- `base_tags`: legacy fallback only; generated logs still use exactly one task tag.

## Obsidian Template

Your template must include frontmatter. The script only fills properties that already exist in the template, preserving their names and order.

Common template:

```markdown
---
Date:
Project:
tags:
Summary:
---

{{WORKLOG_CONTENT}}
```

Supported content placeholders:

- `{{WORKLOG_CONTENT}}`
- `{{worklog_content}}`
- `{{codex_worklog}}`

If no placeholder is present, the work log block is appended to the end of the template.

## Generate A Log

Ask Codex to use `$worklog`, then provide a project name and one task tag. The skill summarizes only the current chat unless you explicitly ask it to use more context.

Manual dry run:

```bash
python scripts/worklog_io.py write \
  --project-name "Project Name" \
  --task-tag task/tag \
  --summary "Short summary" \
  --body-file /tmp/worklog-body.md \
  --dry-run
```

Write the log:

```bash
python scripts/worklog_io.py write \
  --project-name "Project Name" \
  --task-tag task/tag \
  --summary "Short summary" \
  --body-file /tmp/worklog-body.md
```

Notes:

- Task tags can be passed with or without a leading `#`.
- Spaces in task tags are normalized to `_`.
- The script writes exactly one task tag to frontmatter.
- Same-day logs for the same project and task tag are appended to the existing note.
- Different same-day project/task combinations are numbered as `MM.DD.md`, `MM.DD-1.md`, `MM.DD-2.md`, and so on.

## Restore Memory

Find all logs for a project:

```bash
python scripts/worklog_io.py find --project-name "Project Name" --format markdown
```

Find all logs for one task tag:

```bash
python scripts/worklog_io.py find --task-tag task/tag --format markdown
```

Codex should read every returned log and summarize:

- current state
- completed work
- key decisions
- active TODOs
- blockers and risks
- files, commands, or vault notes that matter next

## Validate

Check the resolved config:

```bash
python scripts/worklog_io.py status
```

Validate the skill package by path:

```bash
python /path/to/skill-creator/scripts/quick_validate.py /path/to/worklog
```

Check that no local packaging files were included:

```bash
find /path/to/worklog -name ".DS_Store" -print
```

If this folder is named `worklog-generic` while its `SKILL.md` still says `name: worklog`, do not test it by typing `$worklog` on a machine that also has another `worklog` skill installed. Run `quick_validate.py` and `scripts/worklog_io.py` with explicit paths instead.

## Troubleshooting

- `Config not found`: copy `config.example.json` to `config.json` and fill in the required fields.
- `Missing config field(s)`: fill in `vault_path`, `template_path`, and `worklog_folder`.
- `Template path does not exist`: check that `template_path` is relative to the vault root.
- `Invalid tag`: remove punctuation, leading numbers, or empty nested tag segments.
- No logs found in `find`: confirm that the requested `Project` value or task tag exists in the target worklog folder.
