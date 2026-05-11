---
name: worklog
description: Generate current-chat Codex work logs in an Obsidian vault using a configured daily template, stage local figures into an attachments folder, and restore project or task memory using Project plus a single task tag.
---

# Worklog

Use this skill when the user wants to create an Obsidian work log from the current Codex chat, stage existing local figures for that note, or recover project/task context from prior work logs.

## Configuration

Before doing file work, read `config.json` in this skill folder. If it does not exist, tell the user to copy `config.example.json` to `config.json` and fill in their own paths.

Required fields:

- `vault_path`: absolute path to the Obsidian vault root.
- `template_path`: path to the daily template, relative to the vault root.
- `worklog_folder`: destination folder for work logs, relative to the vault root.
- `timezone`: IANA time zone such as `America/New_York`, or `local` to use the system time zone.
- `language`: `auto` by default. Write log bodies and Summary values in the language requested by the user; if unspecified, follow the current conversation language.
- `base_tags`: legacy fallback only. Work logs must still contain exactly one task tag.

If `vault_path`, `template_path`, or `worklog_folder` is empty, ask the user for those paths before writing. Do not guess.

Use `scripts/worklog_io.py` for deterministic file operations:

```bash
python scripts/worklog_io.py status
printf '%s' '[{"source":"/absolute/path/to/figure-a.png"},{"source":"/absolute/path/to/figure-b.png","name":"result-comparison.png"}]' | python scripts/worklog_io.py stage-attachments --manifest-stdin --dry-run
python scripts/worklog_io.py write --project-name "Project Name" --task-tag task/tag --summary "① Complete one parameter test and confirm the main trend；② Organize the key figure and mark one part for review" --body-file /tmp/worklog-body.md --dry-run
python scripts/worklog_io.py write --project-name "Project Name" --task-tag task/tag --summary "① Complete one parameter test and confirm the main trend；② Organize the key figure and mark one part for review" --body-file /tmp/worklog-body.md
python scripts/worklog_io.py write --project-name "Project Name" --task-tag task/tag --summary "① Merge the updated result note；② Refresh the figure reference after review" --body-file /tmp/worklog-body.md --replace
python scripts/worklog_io.py find --project-name "Project Name" --format markdown
python scripts/worklog_io.py find --task-tag task/tag --format markdown
```

## Generate A Work Log

Default scope is only the current Codex chat. Do not read Codex global history, session databases, or other threads unless the user explicitly asks.

1. Get the project name and one task tag from the user or the current request. Use a legal Obsidian tag without leading `#`; spaces are normalized to `_`.
2. Summarize the current chat into a concise Markdown body. Prefer these sections unless the user gives another template:
   - Today goal
   - Key results
   - Parameter settings
   - Attention
   - Next steps
3. Write the body in the requested language. If no language is specified, follow the conversation language.
4. Write `Key results` as result bullets, not operation logs:
   - Each top-level bullet is one result or one meaningful research subtask.
   - Keep interpretation and discussion merged into that result bullet.
   - Do not create a separate `Result interpretation` or `Current interpretation` section.
   - If a result has a key figure, stage the existing local image into `attachments/` and embed it under the corresponding result bullet.
   - Keep figure notes short: say what the figure is, and keep the conclusion in the result bullet.
5. If figures are needed, stage them first with `stage-attachments`:
   - The manifest must be passed through stdin as a JSON array.
   - Do not create persistent manifest files in the vault or skill folder.
   - The command copies images into `<worklog_folder>/attachments/` and returns `embed_path` values such as `attachments/result-comparison.png`.
   - Embed figures with Obsidian syntax such as `![[attachments/result-comparison.png]]`.
6. Run the script with `write`. Start with `--dry-run` when using a new vault, template, or folder. If the script reports an existing same-day same-task note, read that note, merge the new work into one consolidated body, and rerun `write` with `--replace`.
7. The script inserts the body into the configured template. If the template contains `{{WORKLOG_CONTENT}}`, `{{worklog_content}}`, or `{{codex_worklog}}`, the body is inserted there; otherwise it is appended.
8. Frontmatter properties must exactly match the configured template's property names and order. The script fills only properties already present in the template:
   - `Date`: the work log date.
   - `Project`: the project name. If the task tag already exists in prior logs, reuse that existing `Project`; otherwise use the provided project name.
   - `tags`: exactly one task tag. This is the thread task or work-content label under the project, not the project itself.
   - `Summary`: a concise one-line summary in the requested or configured language.
   - If `Summary` includes multiple sub-items, keep them on one line and separate them as `① ...；② ...；③ ...`.
   - Each numbered Summary segment must represent one independent subtask and may combine the action with the result for that subtask.
   - Do not put next steps into `Summary`.

Suggested generic body shape:

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

File naming is managed by the script:

- First log on a day: `MM.DD.md`.
- Second different project or task on the same day: rename `MM.DD.md` to `MM.DD-1.md`, then create `MM.DD-2.md`.
- Third and later different projects or tasks on the same day: create `MM.DD-3.md`, `MM.DD-4.md`, and so on.
- Same project and same task tag on the same day: merge the new work into that task's existing file and write it back with `--replace`, keeping one consolidated worklog block.
- Same project but different task tag on the same day: create a separate numbered file.

The metadata hierarchy is `Project` -> `tags`: `Project` is the parent project, and the single `tags` value is the current thread task/work content. When writing, prefer existing metadata found for that task tag; if none exists, use the provided project name and task tag.

## Restore Project Memory

When a new chat needs project context:

1. Ask for the project name or task tag if neither is provided.
2. Run `find --project-name PROJECT --format markdown` for project-level memory, or `find --task-tag TAG --format markdown` for a thread/task.
3. Read every returned log. Do not limit to the most recent notes.
4. Produce a compact project memory summary:
   - current goal or active question
   - key results
   - parameter settings that still matter
   - attention points and risks
   - next steps

Keep the restored memory factual. If logs conflict, mention the conflict and prefer the newest dated log.

## Obsidian Rules

- Store exactly one task tag in frontmatter without leading `#`; convert spaces to `_`.
- Do not add frontmatter properties that are not in the template.
- Fill `Project` with the existing project value for the task tag when available; otherwise use the provided project name.
- Preserve existing template content where practical.
- Do not execute Templater or other Obsidian plugin code embedded in templates.
- Use wikilinks only for actual vault notes and local figure embeds; use normal Markdown links for external URLs.
- When staging figures, copy them into `attachments/` through `stage-attachments`; do not leave persistent manifest files behind.
