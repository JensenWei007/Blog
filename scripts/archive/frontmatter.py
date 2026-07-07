"""Markdown Front Matter 解析与日期解析。"""

import re
from datetime import datetime
from pathlib import Path


def parse_front_matter(md_path: Path) -> tuple[dict, str]:
    """解析 markdown 的 YAML Front Matter，返回 (meta, body)。"""
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not match:
        print(f"  ⚠ 警告：{md_path.name} 没有找到 Front Matter，使用空元数据")
        return {}, content

    front_matter_raw = match.group(1)
    body = content[match.end():]

    meta = {}
    for line in front_matter_raw.strip().split("\n"):
        line = line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        m = re.match(r"^(\w[\w-]*)\s*:\s*(.*)", line)
        if m:
            key = m.group(1).strip()
            value = m.group(2).strip()
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            meta[key] = value

    return meta, body


def parse_date_to_archive_path(date_str: str) -> tuple[int, int, int]:
    """解析日期为 (year, month, day)。支持 ISO / 显示格式。"""
    if not date_str:
        raise ValueError("日期为空")
    date_str = date_str.strip()
    formats = [
        "%Y-%m-%d", "%Y/%m/%d",
        "%d %B, %Y", "%d %B %Y",
        "%B %d, %Y", "%B %d %Y",
        "%Y-%m-%dT%H:%M:%S",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return (dt.year, dt.month, dt.day)
        except ValueError:
            continue
    raise ValueError(f"无法解析日期格式: '{date_str}'")
