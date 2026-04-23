# Worklog

`worklog` is a Codex skill for writing the current Codex chat into an Obsidian work log, then restoring project or task memory from those logs later.

It is designed for users who keep project notes in Obsidian and want a repeatable way to preserve decisions, completed work, commands, blockers, and next steps.

## Install

### Option 1: Install to `.agents` with npx

```bash
npx skills add git@github.com:Youyuyoyuu/workflow-obsidian.git --skill worklog
```

### Option 2: Manual install

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
- `Project` is the parent project; `tags` is the current task or work-content label.
- If a task tag already exists in prior logs, the script reuses that tag's existing `Project`; otherwise it uses `--project-name`.
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

---

# Worklog 中文说明

`worklog` 是一个 Codex skill，用于把当前 Codex 聊天写入 Obsidian 工作日志，并在之后从这些日志中恢复项目或任务记忆。

它适合使用 Obsidian 管理项目笔记的用户，用来稳定记录决策、完成事项、命令、阻塞点和下一步。

## 安装

### 方法 1：用 npx 安装到 `.agents`

```bash
npx skills add git@github.com:Youyuyoyuu/workflow-obsidian.git --skill worklog
```

### 方法 2：手动安装

把这个 skill 文件夹放到你的 Codex skills 目录：

```bash
~/.codex/skills/worklog
```

文件夹应包含：

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


## 配置

复制示例配置，并填写你自己的 Obsidian 路径：

```bash
cp config.example.json config.json
```

示例：

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

字段说明：

- `vault_path`：Obsidian vault 根目录的绝对路径。
- `template_path`：相对于 vault 根目录的日记模板路径。
- `worklog_folder`：生成工作日志的目标文件夹，相对于 vault 根目录。
- `timezone`：使用 `local` 表示系统本地时区，也可以填写 IANA 时区，例如 `America/New_York`。
- `language`：`auto` 表示跟随用户请求或当前对话语言。
- `base_tags`：仅用于兼容旧逻辑；生成的日志仍然只写入一个任务 tag。

## Obsidian 模板

模板必须包含 frontmatter。脚本只会填充模板中已经存在的属性，并保留属性名称和顺序。

常用模板：

```markdown
---
Date:
Project:
tags:
Summary:
---

{{WORKLOG_CONTENT}}
```

支持的正文占位符：

- `{{WORKLOG_CONTENT}}`
- `{{worklog_content}}`
- `{{codex_worklog}}`

如果模板中没有这些占位符，工作日志块会追加到模板末尾。

## 生成日志

让 Codex 使用 `$worklog`，并提供项目名和一个任务 tag。除非你明确要求使用更多上下文，否则 skill 只总结当前聊天。

手动 dry run：

```bash
python scripts/worklog_io.py write \
  --project-name "Project Name" \
  --task-tag task/tag \
  --summary "Short summary" \
  --body-file /tmp/worklog-body.md \
  --dry-run
```

正式写入：

```bash
python scripts/worklog_io.py write \
  --project-name "Project Name" \
  --task-tag task/tag \
  --summary "Short summary" \
  --body-file /tmp/worklog-body.md
```

注意：

- 任务 tag 可以带 `#`，也可以不带。
- 任务 tag 中的空格会被转换为 `_`。
- 脚本只会向 frontmatter 写入一个任务 tag。
- `Project` 是父项目；`tags` 是当前任务或工作内容标签。
- 如果某个任务 tag 已经出现在历史日志中，脚本会复用该 tag 既有的 `Project`；否则使用 `--project-name`。
- 同一天、同项目、同任务 tag 的日志会追加到已有笔记。
- 同一天的不同项目或任务组合会按 `MM.DD.md`、`MM.DD-1.md`、`MM.DD-2.md` 等方式编号。

## 恢复记忆

查找某个项目的全部日志：

```bash
python scripts/worklog_io.py find --project-name "Project Name" --format markdown
```

查找某个任务 tag 的全部日志：

```bash
python scripts/worklog_io.py find --task-tag task/tag --format markdown
```

Codex 应读取所有返回的日志，并总结：

- 当前状态
- 已完成工作
- 关键决策
- 当前 TODO
- 阻塞点和风险
- 后续重要的文件、命令或 vault 笔记

## 验证

检查解析后的配置：

```bash
python scripts/worklog_io.py status
```

按路径验证 skill 包：

```bash
python /path/to/skill-creator/scripts/quick_validate.py /path/to/worklog
```

检查是否误包含本机打包文件：

```bash
find /path/to/worklog -name ".DS_Store" -print
```

如果这个文件夹名是 `worklog-generic`，但 `SKILL.md` 里仍写着 `name: worklog`，并且本机也安装了另一个 `worklog` skill，请不要通过输入 `$worklog` 来测试它。应该用明确路径运行 `quick_validate.py` 和 `scripts/worklog_io.py`。

## 常见问题

- `Config not found`：把 `config.example.json` 复制为 `config.json`，并填写必需字段。
- `Missing config field(s)`：填写 `vault_path`、`template_path` 和 `worklog_folder`。
- `Template path does not exist`：确认 `template_path` 是相对于 vault 根目录的路径。
- `Invalid tag`：移除标点、开头数字或空的嵌套 tag 片段。
- `find` 找不到日志：确认目标 worklog 文件夹中存在对应的 `Project` 值或任务 tag。
