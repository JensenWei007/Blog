"""新文章摄入：解析 md → 分配 id → 加入 all.json → 生成归档。"""

import json
import shutil
from datetime import datetime
from pathlib import Path

from .config import ARCHIVE_ROOT, MD_DIR
from .frontmatter import parse_front_matter, parse_date_to_archive_path
from .alljson import load_all_json, save_all_json, next_id, build_cat_id_map
from .entry import process_entry, compute_entry_links


def ingest_new_post(md_path: Path, template: str, dry_run: bool = False) -> bool:
    """
    摄入一篇新文章：
    1. 解析 Front Matter
    2. 分配 id
    3. 复制到 md/{id}.md
    4. 添加条目到 all.json（含自动计算的 link 字段）
    5. 生成归档 HTML
    """
    if not md_path.is_file():
        print(f"✗ 错误：文件不存在: {md_path}")
        return False

    meta, body = parse_front_matter(md_path)
    title = meta.get("title", md_path.stem)

    entries = load_all_json()
    new_id = next_id(entries)
    print(f"📝 新文章: \"{title}\"  →  分配 id={new_id}")

    MD_DIR.mkdir(parents=True, exist_ok=True)
    dest_md = MD_DIR / f"{new_id}.md"
    if not dry_run:
        shutil.copy2(md_path, dest_md)
        print(f"  ✓ 已复制: {md_path.name} → {dest_md}")

    date_str = meta.get("date", datetime.now().strftime("%Y-%m-%d"))
    try:
        year, month, day = parse_date_to_archive_path(date_str)
    except ValueError:
        year, month, day = datetime.now().year, datetime.now().month, datetime.now().day

    try:
        display_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%-d %B, %Y")
    except ValueError:
        display_date = date_str

    new_category = meta.get("category", "")
    cat_id_map = build_cat_id_map(entries)
    if new_category and new_category not in cat_id_map:
        cat_id_map[new_category] = len(cat_id_map)

    new_entry = {
        "id": new_id,
        "title": title,
        "date": display_date,
        "category": new_category,
        "description": meta.get("description", ""),
        "source": f"md/{new_id}.md",
    }
    if meta.get("image"):
        new_entry["image"] = meta["image"]
    if meta.get("imageAlt"):
        new_entry["imageAlt"] = meta["imageAlt"]

    compute_entry_links(new_entry, cat_id_map)

    if dry_run:
        print(f"  → 将添加到 all.json: {json.dumps(new_entry, ensure_ascii=False, indent=2)}")
        archive_dir = ARCHIVE_ROOT / str(year) / str(month) / str(day) / str(new_id)
        print(f"  → 将归档到: {archive_dir}")
        return True
    else:
        entries.append(new_entry)
        save_all_json(entries)
        print(f"  ✓ 已添加到 all.json (id={new_id})")

    result = process_entry(new_entry, template, dry_run=False)
    return result != "fail"
