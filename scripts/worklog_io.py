#!/usr/bin/env python3
"""Deterministic file operations for the worklog skill."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None


DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "config.json"
DEFAULT_CONFIG_EXAMPLE = Path(__file__).resolve().parents[1] / "config.example.json"
DATE_RE = re.compile(r"^\s*(\d{4}-\d{2}-\d{2})\s*$")
DAILY_RE_TEMPLATE = r"^{prefix}(?:-(?P<seq>\d+))?\.md$"
INLINE_TAG_RE = re.compile(r"(?<![\w/-])#([^\s#\[\]\|,;:'\"<>]+)")
PLACEHOLDERS = ("{{WORKLOG_CONTENT}}", "{{worklog_content}}", "{{codex_worklog}}")


class WorklogError(Exception):
    """User-facing error."""


@dataclass(frozen=True)
class Config:
    path: Path
    vault_path: Path | None
    template_path: Path | None
    worklog_dir: Path | None
    timezone: str
    language: str
    base_tags: tuple[str, ...]
    missing: tuple[str, ...]


@dataclass(frozen=True)
class DailyFile:
    path: Path
    seq: int


def normalize_tag(raw: str) -> str:
    tag = str(raw).strip()
    while tag.startswith("#"):
        tag = tag[1:]
    tag = "_".join(tag.split())
    tag = tag.strip().strip("/")
    if not tag:
        raise WorklogError("Task tag is required.")
    if tag[0].isdigit():
        raise WorklogError(f"Invalid tag '{raw}': Obsidian tags cannot start with a number.")
    if any(ch in tag for ch in "#[]|,;:'\"<>"):
        raise WorklogError(f"Invalid tag '{raw}': remove punctuation or a leading #.")
    if "//" in tag:
        raise WorklogError(f"Invalid tag '{raw}': empty nested tag segment.")
    return tag


def load_config(path: Path, require_template: bool = True) -> Config:
    if not path.exists():
        hint = ""
        if path == DEFAULT_CONFIG and DEFAULT_CONFIG_EXAMPLE.exists():
            hint = f" Create it by copying {DEFAULT_CONFIG_EXAMPLE.name} to {path.name} and filling in your own paths."
        raise WorklogError(f"Config not found: {path}.{hint}")
    data = json.loads(path.read_text(encoding="utf-8"))
    missing: list[str] = []

    vault_raw = str(data.get("vault_path", "")).strip()
    template_raw = str(data.get("template_path", "")).strip()
    folder_raw = str(data.get("worklog_folder", "")).strip()

    if not vault_raw:
        missing.append("vault_path")
    if require_template and not template_raw:
        missing.append("template_path")
    if not folder_raw:
        missing.append("worklog_folder")

    vault = Path(vault_raw).expanduser().resolve() if vault_raw else None
    template = (vault / template_raw).resolve() if vault and template_raw else None
    worklog_dir = (vault / folder_raw).resolve() if vault and folder_raw else None

    tags = tuple(normalize_tag(tag) for tag in data.get("base_tags", ["codex/worklog"]))
    timezone = str(data.get("timezone", "local")).strip() or "local"
    language = str(data.get("language", "auto")).strip() or "auto"

    return Config(
        path=path,
        vault_path=vault,
        template_path=template,
        worklog_dir=worklog_dir,
        timezone=timezone,
        language=language,
        base_tags=tags,
        missing=tuple(missing),
    )


def require_complete(config: Config, need_template: bool = True) -> None:
    if config.missing:
        raise WorklogError("Missing config field(s): " + ", ".join(config.missing))
    if config.vault_path is None or not config.vault_path.exists():
        raise WorklogError(f"Vault path does not exist: {config.vault_path}")
    if need_template and (config.template_path is None or not config.template_path.exists()):
        raise WorklogError(f"Template path does not exist: {config.template_path}")
    if config.worklog_dir is None:
        raise WorklogError("worklog_folder is not configured.")


def selected_date(timezone: str, override: str | None) -> datetime:
    if override:
        return datetime.strptime(override, "%Y-%m-%d")
    if timezone.lower() in ("local", "system"):
        return datetime.now()
    if ZoneInfo is None:
        return datetime.now()
    return datetime.now(ZoneInfo(timezone))


def daily_prefix(dt: datetime) -> str:
    return dt.strftime("%m.%d")


def full_date(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


def read_body(args: argparse.Namespace) -> str:
    if args.body_file:
        return Path(args.body_file).read_text(encoding="utf-8").strip()
    if args.body_stdin:
        return sys.stdin.read().strip()
    raise WorklogError("Provide --body-file or --body-stdin.")


def frontmatter_match(content: str) -> re.Match[str] | None:
    return re.match(r"^---\n(.*?)\n---\n?", content, re.DOTALL)


def split_frontmatter(content: str) -> tuple[str | None, str]:
    match = frontmatter_match(content)
    if not match:
        return None, content
    return match.group(1), content[match.end() :]


def parse_frontmatter_tags(fm: str | None) -> list[str]:
    if not fm:
        return []
    lines = fm.splitlines()
    tags: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        match = re.match(r"^tags:\s*(.*)$", line, re.IGNORECASE)
        if not match:
            i += 1
            continue
        inline = match.group(1).strip()
        if inline:
            if inline.startswith("[") and inline.endswith("]"):
                items = [item.strip().strip("'\"") for item in inline[1:-1].split(",")]
                tags.extend(item for item in items if item)
            else:
                tags.append(inline.strip("'\""))
        i += 1
        while i < len(lines) and (lines[i].startswith(" ") or lines[i].startswith("\t")):
            item = re.sub(r"^\s*-\s*", "", lines[i]).strip().strip("'\"")
            if item:
                tags.append(item)
            i += 1
    cleaned = []
    for tag in tags:
        try:
            cleaned.append(normalize_tag(tag))
        except WorklogError:
            continue
    return cleaned


def parse_frontmatter_properties(fm: str | None) -> dict[str, str]:
    if not fm:
        return {}
    values: dict[str, str] = {}
    for line in fm.splitlines():
        match = re.match(r"^([^:\n]+):\s*(.*)$", line)
        if not match:
            continue
        key = match.group(1).strip().lower()
        values[key] = match.group(2).strip().strip("'\"")
    return values


def extract_property(content: str, key: str) -> str | None:
    fm, _ = split_frontmatter(content)
    value = parse_frontmatter_properties(fm).get(key.lower())
    return value or None


def first_frontmatter_tag(content: str) -> str | None:
    fm, _ = split_frontmatter(content)
    tags = parse_frontmatter_tags(fm)
    return tags[0] if tags else None


def preferred_frontmatter_tag(content: str, preferred: str) -> str | None:
    fm, _ = split_frontmatter(content)
    tags = parse_frontmatter_tags(fm)
    if preferred in tags:
        return preferred
    return tags[0] if tags else None


def extract_tags(content: str) -> set[str]:
    fm, body = split_frontmatter(content)
    tags = set(parse_frontmatter_tags(fm))
    for match in INLINE_TAG_RE.finditer(body):
        try:
            tags.add(normalize_tag(match.group(1)))
        except WorklogError:
            pass
    return tags


def extract_date(content: str) -> str | None:
    value = extract_property(content, "Date") or extract_property(content, "date")
    if not value:
        return None
    match = DATE_RE.match(value)
    return match.group(1) if match else None


def extract_title(content: str) -> str | None:
    return (
        extract_property(content, "Summary")
        or extract_property(content, "Project")
        or extract_property(content, "title")
    )


def ordered_unique(items: Iterable[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def remove_tags_block(lines: list[str]) -> list[str]:
    output: list[str] = []
    i = 0
    while i < len(lines):
        if re.match(r"^tags:\s*", lines[i]):
            i += 1
            while i < len(lines) and (lines[i].startswith(" ") or lines[i].startswith("\t")):
                i += 1
            continue
        output.append(lines[i])
        i += 1
    return output


def has_key(lines: list[str], key: str) -> bool:
    return any(re.match(rf"^{re.escape(key)}\s*:", line) for line in lines)


def ensure_frontmatter(content: str, date_str: str, tags: list[str], title: str) -> str:
    fm, body = split_frontmatter(content)
    if fm is None:
        tag_lines = "\n".join(f"  - {tag}" for tag in tags)
        return f"---\ntitle: {title}\ndate: {date_str}\ntags:\n{tag_lines}\n---\n\n{content.lstrip()}"

    existing_tags = parse_frontmatter_tags(fm)
    merged_tags = ordered_unique(existing_tags + tags)
    lines = remove_tags_block(fm.splitlines())
    if not has_key(lines, "title"):
        lines.insert(0, f"title: {title}")
    if not has_key(lines, "date"):
        insert_at = 1 if has_key(lines, "title") else 0
        lines.insert(insert_at, f"date: {date_str}")
    lines.append("tags:")
    lines.extend(f"  - {tag}" for tag in merged_tags)
    return "---\n" + "\n".join(lines).rstrip() + "\n---\n" + body


def project_name_from_tag(project_tag: str) -> str:
    return project_tag.split("/")[-1].replace("-", " ").replace("_", " ").strip() or project_tag


def template_frontmatter_lines(template: str) -> list[str]:
    fm, _ = split_frontmatter(template)
    if fm is None:
        raise WorklogError("Template must contain frontmatter.")
    return fm.splitlines()


def template_property_value(rendered: str, key: str) -> str:
    fm, _ = split_frontmatter(rendered)
    return parse_frontmatter_properties(fm).get(key.lower(), "")


def apply_template_frontmatter(
    rendered: str,
    template: str,
    date_str: str,
    project_name: str,
    tag: str,
    summary: str,
) -> str:
    _, body = split_frontmatter(rendered)
    properties: list[str] = []
    for line in template_frontmatter_lines(template):
        match = re.match(r"^([^:\n]+):\s*(.*)$", line)
        if not match:
            continue
        key = match.group(1).strip()
        lower = key.lower()
        if lower == "date":
            value = date_str
        elif lower == "project":
            value = project_name
        elif lower in ("tag", "tags"):
            value = tag
        elif lower == "summary":
            value = summary
        else:
            value = template_property_value(rendered, key)
        properties.append(f"{key}: {value}" if value else f"{key}:")
    return "---\n" + "\n".join(properties).rstrip() + "\n---\n" + body


def build_block(body: str, project_name: str, tag: str, date_str: str, generated_at: str) -> str:
    return (
        f'<!-- worklog:block project="{project_name}" tag="{tag}" date="{date_str}" generated="{generated_at}" -->\n'
        f"{body.strip()}\n"
        "<!-- /worklog:block -->"
    )


def render_template(
    template: str,
    block: str,
    date_str: str,
    prefix: str,
    project_name: str,
    tag: str,
    summary: str,
) -> str:
    rendered = template
    replacements = {
        "{{date}}": date_str,
        "{{DATE}}": date_str,
        "{{mm_dd}}": prefix,
        "{{MM_DD}}": prefix,
        "{{project_name}}": project_name,
        "{{PROJECT_NAME}}": project_name,
        "{{project_tag}}": tag,
        "{{PROJECT_TAG}}": tag,
        "{{tag}}": tag,
        "{{tags}}": tag,
        "{{summary}}": summary,
        "{{SUMMARY}}": summary,
        "{{title}}": f"{prefix} {project_name}",
    }
    for key, value in replacements.items():
        rendered = rendered.replace(key, value)

    for placeholder in PLACEHOLDERS:
        if placeholder in rendered:
            return rendered.replace(placeholder, block)

    rendered = rendered.rstrip()
    return f"{rendered}\n\n{block}\n"


def list_daily_files(worklog_dir: Path, prefix: str) -> list[DailyFile]:
    pattern = re.compile(DAILY_RE_TEMPLATE.format(prefix=re.escape(prefix)))
    files: list[DailyFile] = []
    if not worklog_dir.exists():
        return files
    for path in worklog_dir.iterdir():
        if not path.is_file():
            continue
        match = pattern.match(path.name)
        if not match:
            continue
        seq = int(match.group("seq") or "0")
        files.append(DailyFile(path=path, seq=seq))
    return sorted(files, key=lambda item: (item.seq, item.path.name))


def same_task_file(files: list[DailyFile], task_tag: str, date_str: str) -> Path | None:
    for item in files:
        content = item.path.read_text(encoding="utf-8")
        note_date = extract_date(content)
        if note_date not in (None, date_str):
            continue
        if task_tag in extract_tags(content):
            return item.path
    return None


def existing_project_for_task(worklog_dir: Path, task_tag: str) -> str | None:
    if not worklog_dir.exists():
        return None
    candidates: list[tuple[str, int, str]] = []
    for path in worklog_dir.rglob("*.md"):
        content = path.read_text(encoding="utf-8")
        if task_tag not in extract_tags(content):
            continue
        project = extract_property(content, "Project")
        if project:
            candidates.append((str(path), sequence_from_name(path), project))
    if not candidates:
        return None
    candidates.sort()
    return candidates[-1][2]


def next_target(worklog_dir: Path, prefix: str, files: list[DailyFile]) -> tuple[Path, list[tuple[Path, Path]]]:
    unsuffixed = worklog_dir / f"{prefix}.md"
    if not files:
        return unsuffixed, []

    renames: list[tuple[Path, Path]] = []
    seqs = [item.seq for item in files]
    if any(item.seq == 0 for item in files):
        first = worklog_dir / f"{prefix}-1.md"
        if first.exists():
            raise WorklogError(f"Cannot rename {unsuffixed.name}: {first.name} already exists.")
        renames.append((unsuffixed, first))
        seqs = [1 if seq == 0 else seq for seq in seqs]

    next_seq = max(seqs, default=1) + 1
    target = worklog_dir / f"{prefix}-{next_seq}.md"
    if target.exists():
        raise WorklogError(f"Target already exists: {target}")
    return target, renames


def relative_to_vault(path: Path, vault: Path | None) -> str:
    if vault is None:
        return str(path)
    try:
        return str(path.relative_to(vault))
    except ValueError:
        return str(path)


def cmd_status(args: argparse.Namespace) -> int:
    config = load_config(args.config, require_template=True)
    payload = {
        "config": str(config.path),
        "complete": not config.missing,
        "missing": list(config.missing),
        "vault_path": str(config.vault_path) if config.vault_path else "",
        "template_path": str(config.template_path) if config.template_path else "",
        "worklog_dir": str(config.worklog_dir) if config.worklog_dir else "",
        "timezone": config.timezone,
        "language": config.language,
        "base_tags": list(config.base_tags),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_write(args: argparse.Namespace) -> int:
    config = load_config(args.config, require_template=True)
    require_complete(config, need_template=True)
    assert config.template_path is not None
    assert config.worklog_dir is not None

    task_tag = normalize_tag(args.task_tag)
    requested_project_name = args.project_name.strip() if args.project_name else project_name_from_tag(task_tag)
    summary = args.summary.strip() if args.summary else ""
    dt = selected_date(config.timezone, args.date)
    date_str = full_date(dt)
    prefix = daily_prefix(dt)
    generated_at = dt.isoformat()

    body = read_body(args)
    template = config.template_path.read_text(encoding="utf-8")

    files = list_daily_files(config.worklog_dir, prefix)
    existing = same_task_file(files, task_tag, date_str)
    existing_text = existing.read_text(encoding="utf-8") if existing else ""
    project_name = (
        extract_property(existing_text, "Project")
        or existing_project_for_task(config.worklog_dir, task_tag)
        or requested_project_name
    )
    tag = preferred_frontmatter_tag(existing_text, task_tag) or task_tag
    block = build_block(body, project_name, tag, date_str, generated_at)
    rendered = render_template(template, block, date_str, prefix, project_name, tag, summary)
    rendered = apply_template_frontmatter(rendered, template, date_str, project_name, tag, summary)

    renames: list[tuple[Path, Path]] = []
    action = "created"

    if existing:
        target = existing
        if args.replace:
            output = rendered
            action = "replaced"
        else:
            raise WorklogError(
                "Existing same-day same-task note found. Merge the new work into the existing note body, "
                "then rerun write with --replace to keep one consolidated worklog block."
            )
    else:
        target, renames = next_target(config.worklog_dir, prefix, files)
        output = rendered

    payload = {
        "action": action,
        "dry_run": args.dry_run,
        "path": str(target),
        "vault_relative_path": relative_to_vault(target, config.vault_path),
        "renames": [
            {"from": str(source), "to": str(destination)}
            for source, destination in renames
        ],
        "project_tag": task_tag,
        "task_tag": task_tag,
        "project_name": project_name,
        "tag": tag,
        "date": date_str,
    }

    if args.dry_run:
        payload["content"] = output
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    config.worklog_dir.mkdir(parents=True, exist_ok=True)
    for source, destination in renames:
        source.rename(destination)
    target.write_text(output.rstrip() + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def sequence_from_name(path: Path) -> int:
    match = re.match(r"^\d{2}\.\d{2}(?:-(\d+))?\.md$", path.name)
    if not match:
        return 999999
    return int(match.group(1) or "0")


def inferred_month_day(path: Path) -> str:
    match = re.match(r"^(\d{2}\.\d{2})", path.name)
    return match.group(1) if match else "99.99"


def matching_logs(
    worklog_dir: Path,
    task_tag: str | None = None,
    project_name: str | None = None,
) -> list[tuple[Path, str, str | None, str | None]]:
    matches: list[tuple[Path, str, str | None, str | None]] = []
    if not worklog_dir.exists():
        return matches
    for path in worklog_dir.rglob("*.md"):
        content = path.read_text(encoding="utf-8")
        if task_tag and task_tag not in extract_tags(content):
            continue
        if project_name and extract_property(content, "Project") != project_name:
            continue
        matches.append((path, content, extract_date(content), extract_title(content)))
    return sorted(
        matches,
        key=lambda item: (
            item[2] or "9999-99-99",
            inferred_month_day(item[0]),
            sequence_from_name(item[0]),
            item[0].name,
        ),
    )


def cmd_find(args: argparse.Namespace) -> int:
    config = load_config(args.config, require_template=False)
    require_complete(config, need_template=False)
    assert config.worklog_dir is not None

    task_tag = normalize_tag(args.task_tag) if args.task_tag else None
    project_name = args.project_name.strip() if args.project_name else None
    if not task_tag and not project_name:
        raise WorklogError("Provide --project-name or --task-tag.")
    matches = matching_logs(config.worklog_dir, task_tag=task_tag, project_name=project_name)

    if args.format == "paths":
        for path, _, _, _ in matches:
            print(path)
        return 0

    if args.format == "json":
        payload = []
        for path, content, date_str, title in matches:
            item = {
                "path": str(path),
                "vault_relative_path": relative_to_vault(path, config.vault_path),
                "date": date_str or "",
                "title": title or "",
            }
            if args.include_content:
                item["content"] = content
            payload.append(item)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    for path, content, date_str, title in matches:
        rel = relative_to_vault(path, config.vault_path)
        print(f'<!-- worklog:file path="{rel}" date="{date_str or ""}" title="{title or ""}" -->')
        print(content.rstrip())
        print("<!-- /worklog:file -->")
        print()
    return 0


def build_parser() -> argparse.ArgumentParser:
    config_parent = argparse.ArgumentParser(add_help=False)
    config_parent.add_argument("--config", type=Path, default=argparse.SUPPRESS, help="Path to config.json")

    parser = argparse.ArgumentParser(description="Worklog skill file operations")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="Path to config.json")
    subparsers = parser.add_subparsers(dest="command", required=True)

    status = subparsers.add_parser("status", parents=[config_parent], help="Show resolved configuration")
    status.set_defaults(func=cmd_status)

    write = subparsers.add_parser("write", parents=[config_parent], help="Create or update a work log")
    write.add_argument(
        "--task-tag",
        "--project-tag",
        dest="task_tag",
        required=True,
        help="Single Obsidian task tag, with or without leading #. Spaces are converted to underscores. --project-tag is kept as a compatibility alias.",
    )
    write.add_argument("--project-name", help="Project name to write into the template Project property")
    write.add_argument(
        "--summary",
        help="One-line Summary property matching the requested or configured language.",
    )
    write.add_argument("--body-file", help="Markdown file containing the summarized work log body")
    write.add_argument("--body-stdin", action="store_true", help="Read the summarized work log body from stdin")
    write.add_argument("--date", help="Override date as YYYY-MM-DD")
    write.add_argument("--dry-run", action="store_true", help="Print the planned write without changing files")
    write.add_argument("--replace", action="store_true", help="Replace an existing same-day same-task note with a merged body")
    write.set_defaults(func=cmd_write)

    find = subparsers.add_parser("find", parents=[config_parent], help="Find work logs by project name or task tag")
    find.add_argument("--project-name", help="Project property value to search")
    find.add_argument(
        "--task-tag",
        "--project-tag",
        dest="task_tag",
        help="Single Obsidian task tag to search. Spaces are converted to underscores. --project-tag is kept as a compatibility alias.",
    )
    find.add_argument("--format", choices=("paths", "json", "markdown"), default="paths")
    find.add_argument("--include-content", action="store_true", help="Include note content in JSON output")
    find.set_defaults(func=cmd_find)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except WorklogError as exc:
        print(f"worklog_io: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
