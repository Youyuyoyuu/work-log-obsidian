---
name: worklog
description: Generate current-chat Codex work logs in an Obsidian vault using a configured daily template, and restore project or task memory using Project plus a single task tag.
---

# Worklog

Use this skill when the user wants to create an Obsidian work log from the current Codex chat, or recover project/task context from prior work logs.

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
python scripts/worklog_io.py write --project-name "Project Name" --task-tag task/tag --summary "Short summary" --body-file /tmp/worklog-body.md --dry-run
python scripts/worklog_io.py write --project-name "Project Name" --task-tag task/tag --summary "Short summary" --body-file /tmp/worklog-body.md
python scripts/worklog_io.py find --project-name "Project Name" --format markdown
python scripts/worklog_io.py find --task-tag task/tag --format markdown
```

## Generate A Work Log

Default scope is only the current Codex chat. Do not read Codex global history, session databases, or other threads unless the user explicitly asks.

1. Get the project name and one task tag from the user or the current request. Use a legal Obsidian tag without leading `#`; spaces are normalized to `_`.
2. Summarize the current chat into a concise Markdown body. Prefer these sections unless the user gives another template:
   - Work log
   - Completed work
   - Key decisions
   - Files and commands
   - Blockers
   - Next steps
3. Write the body in the requested language. If no language is specified, follow the conversation language.
4. Run the script with `write`. Start with `--dry-run` when using a new vault, template, or folder.
5. The script inserts the body into the configured template. If the template contains `{{WORKLOG_CONTENT}}`, `{{worklog_content}}`, or `{{codex_worklog}}`, the body is inserted there; otherwise it is appended.
6. Frontmatter properties must exactly match the configured template's property names and order. The script fills only properties already present in the template:
   - `Date`: the work log date.
   - `Project`: the project name. If the task tag already exists in prior logs, reuse that existing `Project`; otherwise use the provided project name.
   - `tags`: exactly one task tag. This is the thread task or work-content label under the project, not the project itself.
   - `Summary`: a concise one-line summary in the requested or configured language.

File naming is managed by the script:

- First log on a day: `MM.DD.md`.
- Second different project or task on the same day: rename `MM.DD.md` to `MM.DD-1.md`, then create `MM.DD-2.md`.
- Third and later different projects or tasks on the same day: create `MM.DD-3.md`, `MM.DD-4.md`, and so on.
- Same project and same task tag on the same day: append an update block to that task's existing file instead of creating a new numbered file.
- Same project but different task tag on the same day: create a separate numbered file.

The metadata hierarchy is `Project` -> `tags`: `Project` is the parent project, and the single `tags` value is the current thread task/work content. When writing, prefer existing metadata found for that task tag; if none exists, use the provided project name and task tag.

## Restore Project Memory

When a new chat needs project context:

1. Ask for the project name or task tag if neither is provided.
2. Run `find --project-name PROJECT --format markdown` for project-level memory, or `find --task-tag TAG --format markdown` for a thread/task.
3. Read every returned log. Do not limit to the most recent notes.
4. Produce a compact project memory summary:
   - current state
   - completed work
   - key decisions
   - active TODOs
   - blockers and risks
   - files, commands, or vault notes that matter next

Keep the restored memory factual. If logs conflict, mention the conflict and prefer the newest dated log.

## Obsidian Rules

- Store exactly one task tag in frontmatter without leading `#`; convert spaces to `_`.
- Do not add frontmatter properties that are not in the template.
- Fill `Project` with the existing project value for the task tag when available; otherwise use the provided project name.
- Preserve existing template content where practical.
- Do not execute Templater or other Obsidian plugin code embedded in templates.
- Use wikilinks only for actual vault notes; use normal Markdown links for external URLs.
