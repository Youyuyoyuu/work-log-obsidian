# Worklog

`worklog` is a Codex skill for writing the current Codex chat into an Obsidian work log, staging existing local figures into an `attachments/` folder, and restoring project or task memory from those logs later.

It is designed as a general research-style logging workflow: summarize key results, keep parameter settings together with the result they support, and embed important figures directly in the note.

## Install

### Option 1: Install to `.agents` with npx

```bash
npx skills add git@github.com:Youyuyoyuu/work-log-obsidian.git --skill worklog
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

Ask Codex to use `$worklog`, then provide a project name and one task tag. The skill summarizes only the current chat unless you explicitly ask it to use more context.

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

Codex should read every returned log and summarize:

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

---

# Worklog 中文说明

`worklog` 是一个 Codex skill，用于把当前 Codex 聊天写入 Obsidian 工作日志，把已有本地图件复制到 `attachments/` 目录中，并在之后从这些日志中恢复项目或任务记忆。

它默认采用通用科研日志风格：以结果为中心组织正文，把参数设置和关键图件放在结果附近，便于后续回看。

## 安装

### 方法 1：用 npx 安装到 `.agents`

```bash
npx skills add git@github.com:Youyuyoyuu/work-log-obsidian.git --skill worklog
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

## 科研日志正文结构

默认正文结构为：

- `## 今日目标`
- `## 核心结果`
- `## 参数设置`
- `## 注意`
- `## 下一步`

建议使用这类泛化写法：

```markdown
## 今日目标
- 验证一组参数是否能够解释当前结果中的主要趋势。

## 核心结果
- 当前参数范围可以解释主要趋势，但其中一个参数仍不稳定，因此现阶段更适合作为阶段性结果，而不是最终结论。
  - 图件：当前结果与参考模式的对比图。
  ![[attachments/result-comparison.png]]

- 多次重复运行后的中间输出保持一致，说明当前流程在进入下一轮检查前是基本稳定的。

## 参数设置
- 数据：当前任务使用的数据。
- 参数：本轮运行的主要参数组。
- 脚本或版本：产生该结果的脚本、笔记本或 commit。
- 输出：保存结果的目录或笔记。

## 注意
- 其中一个参数在相邻设置间变化较明显，因此当前解释应保持保守。

## 下一步
- 围绕不稳定参数再做一轮敏感性检查。
- 下一轮运行后更新对比图。
```

说明：

- `核心结果` 应该写成结果，而不是操作流水账。
- 图件说明尽量简短，只说明“这张图是什么”；结论放在结果主条目里。
- 如果当前日志没有明确的注意项，可以省略 `注意` 这一节。

## 复制图件

如果你已经有本地图件，可以先把它们复制到 worklog 的 `attachments/` 目录，再写日志：

```bash
printf '%s' '[{"source":"/absolute/path/to/figure-a.png"},{"source":"/absolute/path/to/figure-b.png","name":"result-comparison.png"}]' | python scripts/worklog_io.py stage-attachments --manifest-stdin --dry-run
```

正式复制：

```bash
printf '%s' '[{"source":"/absolute/path/to/figure-a.png"},{"source":"/absolute/path/to/figure-b.png","name":"result-comparison.png"}]' | python scripts/worklog_io.py stage-attachments --manifest-stdin
```

行为说明：

- manifest 通过 `stdin` 传入，不需要在磁盘上生成 JSON 文件。
- 图片会被复制到 `<worklog_folder>/attachments/`。
- 命令会返回 JSON，其中包含 `attachments/result-comparison.png` 这样的 `embed_path`。
- 正文中直接使用 `![[attachments/result-comparison.png]]` 即可嵌入。

## 生成日志

让 Codex 使用 `$worklog`，并提供项目名和一个任务 tag。除非你明确要求使用更多上下文，否则 skill 只总结当前聊天。

手动 dry run：

```bash
python scripts/worklog_io.py write \
  --project-name "Project Name" \
  --task-tag task/tag \
  --summary "① 完成一组参数测试并确认主要趋势；② 整理关键图件并标出一个待复核部分" \
  --body-file /tmp/worklog-body.md \
  --dry-run
```

正式写入：

```bash
python scripts/worklog_io.py write \
  --project-name "Project Name" \
  --task-tag task/tag \
  --summary "① 完成一组参数测试并确认主要趋势；② 整理关键图件并标出一个待复核部分" \
  --body-file /tmp/worklog-body.md
```

合并旧正文和新内容后，替换同一天、同项目、同任务 tag 的已有日志：

```bash
python scripts/worklog_io.py write \
  --project-name "Project Name" \
  --task-tag task/tag \
  --summary "① 合并更新后的结果记录；② 在复核后刷新图件引用" \
  --body-file /tmp/worklog-body.md \
  --replace
```

说明：

- 任务 tag 可以带 `#`，也可以不带。
- 任务 tag 中的空格会被转换为 `_`。
- 脚本只会向 frontmatter 写入一个任务 tag。
- `Project` 是父项目；`tags` 是当前任务或工作内容标签。
- 如果某个任务 tag 已经出现在历史日志中，脚本会复用该 tag 既有的 `Project`；否则使用 `--project-name`。
- 同一天、同项目、同任务 tag 的更新必须先合并到已有正文，再用 `--replace` 写回，保持一个 worklog block。
- 同一天的不同项目或任务组合会按 `MM.DD.md`、`MM.DD-1.md`、`MM.DD-2.md` 等方式编号。

## Summary 规则

`Summary` 写在 frontmatter 中，并且必须保持单行。

规则：

- 需要多个子事项时，使用 `① ...；② ...；③ ...`。
- 每个编号只表示一个独立子任务。
- 单个子任务内部可以把动作和结果合并写在一起。
- `Summary` 不写下一步。

推荐的泛化示例：

- `① 完成一组参数测试并确认主要趋势；② 整理关键图件并标出一个待复核部分`
- `① 跑通一轮数据处理并得到初步结果；② 对比参考输出后确认主体模式；③ 汇总当前不稳定参数`

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

- 当前目标或活跃问题
- 核心结果
- 仍然重要的参数设置
- 注意项和风险
- 下一步

## 验证

检查解析后的配置：

```bash
python scripts/worklog_io.py status
```

## 常见问题

- `Config not found`：把 `config.example.json` 复制为 `config.json`，并填写必需字段。
- `Missing config field(s)`：填写 `vault_path`、`template_path` 和 `worklog_folder`。
- `Template path does not exist`：确认 `template_path` 是相对于 vault 根目录的路径。
- `Invalid tag`：移除标点、开头数字或空的嵌套 tag 片段。
- `Attachment manifest is empty` 或 `Invalid attachment manifest JSON`：通过 `stdin` 传入 JSON 数组。
- `Attachment source does not exist`：确认每个图片源路径都正确。
- `find` 找不到日志：确认目标 worklog 文件夹中存在对应的 `Project` 值或任务 tag。
