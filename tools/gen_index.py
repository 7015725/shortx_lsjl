#!/usr/bin/env python3
"""Generate index.json for ShortX repo."""

import json
import os
import re
from pathlib import Path

SHARE_HEADER_RE = re.compile(r"\r?\n###------###\r?\n")


def split_share_content(text: str) -> tuple[str, dict]:
    parts = SHARE_HEADER_RE.split(text.strip(), maxsplit=1)
    if len(parts) < 2:
        return text.strip(), {}
    try:
        header = json.loads(parts[1].strip())
    except json.JSONDecodeError:
        header = {}
    return parts[0].strip(), header


def parse_item(file_path: Path) -> dict | None:
    content, header = split_share_content(file_path.read_text(encoding="utf-8"))

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON parse failed: {file_path.name} - {e}")
        return None

    author = data.get("author", {})
    if isinstance(author, dict):
        author_name = author.get("name", "ShortX")
    else:
        author_name = str(author) if author else "ShortX"

    # versionCode might be string
    version_code = data.get("versionCode", 0)
    try:
        version_code = int(version_code)
    except (ValueError, TypeError):
        version_code = 0

    # updateTimeMillis might be string
    update_time = data.get("lastUpdateTime", 0)
    try:
        update_time = int(update_time)
    except (ValueError, TypeError):
        update_time = 0

    return {
        "id": data.get("id", ""),
        "fileUrl": file_path.name,
        "title": data.get("title", file_path.stem),
        "description": data.get("description", ""),
        "versionCode": version_code,
        "updateTimeMillis": update_time,
        "author": author_name,
        "tags": data.get("tags", []),
        "requireMinShortXProtoVersion": data.get("requireMinShortXProtoVersion", 0),
    }


def scan_dir(root_dir: Path, sub_dir: str) -> list[dict]:
    target = root_dir / sub_dir
    if not target.exists():
        return []

    items = []
    for file_path in target.iterdir():
        if file_path.is_file() and file_path.suffix == ".txt":
            item = parse_item(file_path)
            if item:
                items.append(item)
    return items


def main():
    repo_root = Path(__file__).parent.parent
    if len(os.sys.argv) > 1:
        repo_root = Path(os.sys.argv[1])

    das = scan_dir(repo_root, "da")
    rules = scan_dir(repo_root, "rule")
    codes = scan_dir(repo_root, "code")

    all_items = das + rules + codes
    max_update_time = max((i["updateTimeMillis"] for i in all_items), default=0)

    index = {
        "directActions": das,
        "rules": rules,
        "codeLibraries": codes,
        "updateTimeMillis": max_update_time,
    }

    index_path = repo_root / "index.json"
    index_path.write_text(
        json.dumps(index, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"[OK] index.json generated: {len(das)} DA, {len(rules)} rules, {len(codes)} codes")


if __name__ == "__main__":
    main()
