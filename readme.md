[English](./readme.md) | [中文](./readme.CN.md)

# Worklog

`worklog` is a skill for writing the current chat into an Obsidian work log, staging existing local figures into an `attachments/` folder, and restoring project or task memory from those logs later.

It is designed as a general research-style logging workflow: summarize key results, keep parameter settings together with the result they support, and embed important figures directly in the note.

## Install

### Option 1: Install to `.agents` with npx

```bash
npx skills add git@github.com:Youyuyoyuu/work-log-obsidian.git --skill worklog
```

### Option 2: Manual install

Place this skill folder in your skill directory.

Examples:

```bash
~/.agents/skills/worklog
~/.codex/skills/worklog
```

The folder must contain:

```text
worklog/
├── SKILL.md
├── readme.md
├── readme.CN.md
├── config.example.json
├── agents/
│   └── openai.yaml
└── scripts/
    └── worklog_io.py
```

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
    "research/worklog"
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

If no placeholder is present, the work log block is appended to the end of the template.

## Research-Style Body

The default body shape is:

- `## Today goal`
- `## Key results`
- `## Parameter settings`
- `## Attention`
- `## Next steps`

Suggested generic example:

```markdown
## Today goal
- Verify whether one parameter group can explain the main trend in the current results.

## Key results
- The current parameter range explains the main trend, but one parameter remains unstable, so this is still a provisional result rather than a final conclusion.
  - Figure: comparison between the current result and the reference pattern.
  ![[attachments/result-comparison.png]]

- The intermediate output stays consistent across repeated runs, which suggests the current pipeline is stable enough for the next round of checks.

## Parameter settings
- Data: current working dataset for this task.
- Parameters: main parameter group used in this run.
- Script or version: the script, notebook, or commit used to produce the result.
- Output: the folder or note that stores the generated outputs.

## Attention
- One parameter still changes noticeably across nearby settings, so the interpretation should stay conservative.

## Next steps
- Run one more sensitivity check around the unstable parameter.
- Refresh the comparison figure after the next run.
```

Notes:

- `Key results` should read as results, not a list of operations.
- Keep figure explanations short. Say what the figure is, and keep the interpretation in the result bullet itself.
- If there is no meaningful caution for the current log, `Attention` can be omitted.

## Stage Figures

If you already have local figures, copy them into the worklog `attachments/` directory before writing the note:

```bash
printf '%s' '[{"source":"/absolute/path/to/figure-a.png"},{"source":"/absolute/path/to/figure-b.png","name":"result-comparison.png"}]' | python scripts/worklog_io.py stage-attachments --manifest-stdin --dry-run
```

Run the real copy:

```bash
printf '%s' '[{"source":"/absolute/path/to/figure-a.png"},{"source":"/absolute/path/to/figure-b.png","name":"result-comparison.png"}]' | python scripts/worklog_io.py stage-attachments --manifest-stdin
```

Behavior:

- The manifest is passed through `stdin`; you do not need a JSON file on disk.
- Images are copied into `<worklog_folder>/attachments/`.
- The command returns JSON with `embed_path` values such as `attachments/result-comparison.png`.
- Use those values directly in the note body with `![[attachments/result-comparison.png]]`.

## Generate A Log

Use `$worklog`, then provide a project name and one task tag. The skill summarizes only the current chat unless you explicitly ask it to use more context.

Manual dry run:

```bash
python scripts/worklog_io.py write \
  --project-name "Project Name" \
  --task-tag task/tag \
  --summary "① Complete one parameter test and confirm the main trend；② Organize the key figure and mark one part for review" \
  --body-file /tmp/worklog-body.md \
  --dry-run
```

Write the log:

```bash
python scripts/worklog_io.py write \
  --project-name "Project Name" \
  --task-tag task/tag \
  --summary "① Complete one parameter test and confirm the main trend；② Organize the key figure and mark one part for review" \
  --body-file /tmp/worklog-body.md
```

Replace an existing same-day same-task log after you have merged the old and new body:

```bash
python scripts/worklog_io.py write \
  --project-name "Project Name" \
  --task-tag task/tag \
  --summary "① Merge the updated result note；② Refresh the figure reference after review" \
  --body-file /tmp/worklog-body.md \
  --replace
```

Notes:

- Task tags can be passed with or without a leading `#`.
- Spaces in task tags are normalized to `_`.
- The script writes exactly one task tag to frontmatter.
- `Project` is the parent project; `tags` is the current task or work-content label.
- If a task tag already exists in prior logs, the script reuses that tag's existing `Project`; otherwise it uses `--project-name`.
- Same-day updates for the same project and task tag must be merged into the existing note body and written with `--replace`, keeping one worklog block.
- Different same-day project/task combinations are numbered as `MM.DD.md`, `MM.DD-1.md`, `MM.DD-2.md`, and so on.

## Summary Rules

`Summary` stays in frontmatter and must stay on one line.

Rules:

- Use `① ...；② ...；③ ...` when you need multiple sub-items.
- Each numbered segment must represent one independent subtask.
- A single segment may combine the action and the result for that subtask.
- Do not put next steps into `Summary`.

Suggested generic examples:

- `① Complete one parameter test and confirm the main trend；② Organize the key figure and mark one part for review`
- `① Run one data-processing pass and obtain an initial result；② Compare the reference output and confirm the main pattern；③ Summarize the unstable parameters`

## Restore Memory

Find all logs for a project:

```bash
python scripts/worklog_io.py find --project-name "Project Name" --format markdown
```

Find all logs for one task tag:

```bash
python scripts/worklog_io.py find --task-tag task/tag --format markdown
```

Read every returned log and summarize:

- current goal or active question
- key results
- parameter settings that still matter
- attention points and risks
- next steps

## Validate

Check the resolved config:

```bash
python scripts/worklog_io.py status
```

## Troubleshooting

- `Config not found`: copy `config.example.json` to `config.json` and fill in the required fields.
- `Missing config field(s)`: fill in `vault_path`, `template_path`, and `worklog_folder`.
- `Template path does not exist`: check that `template_path` is relative to the vault root.
- `Invalid tag`: remove punctuation, leading numbers, or empty nested tag segments.
- `Attachment manifest is empty` or `Invalid attachment manifest JSON`: pass a JSON array through `stdin`.
- `Attachment source does not exist`: check that each source image path is correct.
- No logs found in `find`: confirm that the requested `Project` value or task tag exists in the target worklog folder.
