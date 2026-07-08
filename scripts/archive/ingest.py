"""新文章摄入：解析 md → 处理图片 → 分配 id → 加入 all.json → 生成归档。"""

import json
import re
import shutil
from datetime import datetime
from pathlib import Path

from .config import BLOG_ROOT, ARCHIVE_ROOT, MD_DIR, INDEX_JSON, INDEX_MAX_SIZE
from .frontmatter import parse_front_matter, parse_date_to_archive_path
from .alljson import load_all_json, save_all_json, next_id, build_cat_id_map
from .entry import process_entry, compute_entry_links

# 支持的图片扩展名
_IMG_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp'}


def _find_images_in_dir(directory: Path) -> dict[str, Path]:
    """扫描目录下的图片文件，返回 {filename: full_path}。"""
    result = {}
    if not directory.is_dir():
        return result
    for f in directory.iterdir():
        if f.is_file() and f.suffix.lower() in _IMG_EXTS:
            result[f.name] = f
    return result


def _find_image_refs(text: str) -> list[str]:
    """从 markdown 文本中提取所有图片引用的文件名。"""
    refs = []
    # Markdown: ![alt](filename)
    refs.extend(re.findall(r'!\[.*?\]\(([^)]+)\)', text))
    # HTML: <img src="filename">
    refs.extend(re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', text, re.IGNORECASE))
    # 只保留纯文件名（去掉路径前缀）
    cleaned = []
    for r in refs:
        name = Path(r).name
        if name and '.' in name:
            cleaned.append(name)
    return cleaned


def _process_images(md_path: Path, new_id: int, meta: dict, body: str,
                    dry_run: bool = False) -> tuple[str, dict]:
    """
    处理文章中的图片：移动至 images/archive/{id}/，重命名为 0.jpg 等。
    返回 (更新后的 body, 更新后的 meta)。
    """
    new_dir = md_path.parent  # 假定为 new/ 目录
    available = _find_images_in_dir(new_dir)
    if not available:
        return body, meta

    refs = _find_image_refs(body)
    # 也检查 front matter 中的 image 字段
    fm_image = meta.get("image", "").strip()
    if fm_image:
        fm_name = Path(fm_image).name
        if fm_name and fm_name not in refs:
            refs.append(fm_name)

    if not refs:
        return body, meta

    # 去重，保持顺序
    seen = set()
    ordered_refs = []
    for r in refs:
        if r not in seen and r in available:
            seen.add(r)
            ordered_refs.append(r)

    if not ordered_refs:
        return body, meta

    dest_dir = BLOG_ROOT / "images" / "archive" / str(new_id)
    if not dry_run:
        dest_dir.mkdir(parents=True, exist_ok=True)

    mapping = {}  # {original_filename: new_filename}
    for idx, orig_name in enumerate(ordered_refs):
        src_file = available[orig_name]
        ext = src_file.suffix.lower()
        new_name = f"{idx}{ext}"
        mapping[orig_name] = new_name

        if not dry_run:
            shutil.copy2(src_file, dest_dir / new_name)
            print(f"  ✓ 图片: {orig_name} → images/archive/{new_id}/{new_name}")

    # 更新 body 中的图片引用
    for orig_name, new_name in mapping.items():
        new_path = f"images/archive/{new_id}/{new_name}"
        # 替换 markdown 引用: ![alt](orig_name) → ![alt](new_path)
        body = re.sub(
            rf'!\[([^\]]*)\]\([^)]*{re.escape(orig_name)}\)',
            rf'![\1]({new_path})',
            body,
        )
        # 替换 HTML 引用: src="orig_name" → src="new_path"
        body = re.sub(
            rf'src=["\'][^"\']*{re.escape(orig_name)}["\']',
            f'src="{new_path}"',
            body,
            flags=re.IGNORECASE,
        )

    # 更新 front matter 中的 image 字段
    fm_image = meta.get("image", "").strip()
    if fm_image:
        fm_name = Path(fm_image).name
        if fm_name in mapping:
            meta["image"] = f"images/archive/{new_id}/{mapping[fm_name]}"

    return body, meta


def _cleanup_new_dir(md_path: Path) -> None:
    """删除 new/ 目录下的所有文件。"""
    new_dir = md_path.parent
    if new_dir.is_dir():
        for f in new_dir.iterdir():
            if f.is_file():
                f.unlink()
        print(f"  ✓ 已清理: {new_dir}")


def _prepend_index_json(new_id: int) -> None:
    """将 new_id 插入 index.json 队首，超出 INDEX_MAX_SIZE 则截尾。"""
    try:
        if INDEX_JSON.is_file():
            with open(INDEX_JSON, "r", encoding="utf-8") as f:
                ids = json.load(f)
        else:
            ids = []
    except Exception:
        ids = []

    ids = [i for i in ids if i != new_id]
    ids.insert(0, new_id)
    ids = ids[:INDEX_MAX_SIZE]

    INDEX_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(INDEX_JSON, "w", encoding="utf-8") as f:
        json.dump(ids, f, ensure_ascii=False)
    print(f"  ✓ 已更新首页索引: {INDEX_JSON} → {ids}")


def ingest_new_post(md_path: Path, template: str, dry_run: bool = False) -> bool:
    """
    摄入一篇新文章：
    1. 解析 Front Matter
    2. 处理图片（复制到 images/archive/{id}/，重命名，更新引用）
    3. 分配 id，复制 md 到 md/{id}.md
    4. 添加条目到 all.json
    5. 生成归档 HTML
    6. 清理 new/ 目录
    """
    if not md_path.is_file():
        print(f"✗ 错误：文件不存在: {md_path}")
        return False

    meta, body = parse_front_matter(md_path)
    title = meta.get("title", md_path.stem)

    entries = load_all_json()
    new_id = next_id(entries)
    print(f"📝 新文章: \"{title}\"  →  分配 id={new_id}")

    # --- 处理图片 ---
    body, meta = _process_images(md_path, new_id, meta, body, dry_run)

    # --- 写入最终 md ---
    front_lines = []
    for key in ["title", "date", "category", "description", "image", "imageAlt"]:
        val = meta.get(key, "")
        if val:
            front_lines.append(f"{key}: {val}")
    final_md = "---\n" + "\n".join(front_lines) + "\n---\n\n" + body

    MD_DIR.mkdir(parents=True, exist_ok=True)
    dest_md = MD_DIR / f"{new_id}.md"
    if not dry_run:
        with open(dest_md, "w", encoding="utf-8") as f:
            f.write(final_md)
        print(f"  ✓ 已写入: {dest_md}")
    else:
        # dry-run 时仍复制原始文件以保持后续 process_entry 能运行
        shutil.copy2(md_path, dest_md)

    # --- 解析日期 ---
    date_str = meta.get("date", datetime.now().strftime("%Y-%m-%d"))
    try:
        year, month, day = parse_date_to_archive_path(date_str)
    except ValueError:
        year, month, day = datetime.now().year, datetime.now().month, datetime.now().day

    try:
        display_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%-d %B, %Y")
    except ValueError:
        display_date = date_str

    # --- 构建 all.json 条目 ---
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
        _prepend_index_json(new_id)

    result = process_entry(new_entry, template, dry_run=False)

    # --- 清理 new/ 目录 ---
    if result == "success" and not dry_run:
        _cleanup_new_dir(md_path)

    return result != "fail"
