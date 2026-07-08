"""单篇文章处理：读取 md → 生成归档 HTML。"""

import shutil

import markdown

from .config import BLOG_ROOT, ARCHIVE_ROOT, MD_DIR
from .frontmatter import parse_front_matter, parse_date_to_archive_path
from .template import fill_template


def _style_content(html: str) -> str:
    """对 markdown 生成的 HTML 做样式后处理：标题加 class，代码块适配 Prism。"""
    import re

    # 标题：<h1> → <h1 class="h1 mb-3">，依此类推
    for level in range(1, 7):
        html = re.sub(
            rf"<h{level}>",
            rf'<h{level} class="h{level} mb-3">',
            html,
        )

    # 代码块：确保 <pre> 有 Prism 需要的 class
    html = html.replace("<pre>", '<pre class="line-numbers" style="border-radius:8px;">')

    # 表格：按 post-details.html 样式添加 Bootstrap 类
    html = html.replace("<table>",
                        '<table class="table table-bordered text-center text-white table-transparent">')
    html = html.replace("<thead>", '<thead class="bg-dark">')
    html = re.sub(r"<th>", r'<th class="h3" scope="col">', html)

    return html


def compute_entry_links(entry: dict, cat_id_map: dict) -> None:
    """根据条目的日期和分类，自动设置 link / dateLink / categoryLink / imageLink。"""
    from .frontmatter import parse_date_to_archive_path

    eid = entry.get("id")
    date_str = entry.get("date", "")
    try:
        year, month, day = parse_date_to_archive_path(date_str)
    except ValueError:
        return

    entry["link"] = f"archive/{year}/{month}/{day}/{eid}/{eid}.html"
    entry["dateLink"] = f"archive/{year}/{month}/{year}-{month}.html"

    cat_name = entry.get("category", "")
    if cat_name and cat_name in cat_id_map:
        entry["categoryLink"] = f"category/{cat_id_map[cat_name]}.html"
    elif cat_name:
        entry["categoryLink"] = "#"

    if entry.get("image") and not entry.get("imageLink"):
        entry["imageLink"] = entry["link"]


def process_entry(entry: dict, template: str, dry_run: bool = False) -> str:
    """
    处理 all.json 中的单个条目：读取 md 源文件 → 生成归档 HTML。
    返回: "success" | "skip" | "fail"
    """
    entry_id = entry.get("id")
    source_file = entry.get("source") or entry.get("md_file")

    # 找到 md 源文件
    md_path = None
    if source_file:
        candidate = BLOG_ROOT / source_file
        if candidate.is_file():
            md_path = candidate
        else:
            print(f"  ⚠ [id={entry_id}] 指定的源文件不存在: {source_file}")
            return "fail"
    else:
        candidate = MD_DIR / f"{entry_id}.md"
        if candidate.is_file():
            md_path = candidate

    if not md_path:
        print(f"  ℹ [id={entry_id}] 没有关联的 markdown 源文件，跳过")
        return "skip"

    # 解析
    meta, body = parse_front_matter(md_path)
    title = meta.get("title") or entry.get("title", "未命名")

    date_str = meta.get("date") or entry.get("date", "")
    try:
        year, month, day = parse_date_to_archive_path(date_str)
    except ValueError as e:
        print(f"  ✗ [id={entry_id}] 日期解析失败: {e}")
        return "fail"

    archive_dir = ARCHIVE_ROOT / str(year) / str(month) / str(day) / str(entry_id)

    if dry_run:
        print(f"  → [id={entry_id}] 将归档到: {archive_dir}")
        print(f"     标题: {title}  日期: {year}/{month}/{day}  源: {md_path.name}")
        return "success"

    archive_dir.mkdir(parents=True, exist_ok=True)
    print(f"  ✓ [id={entry_id}] 归档目录: {archive_dir}")

    # 复制 md
    dest_md = archive_dir / f"{entry_id}.md"
    shutil.copy2(md_path, dest_md)
    print(f"      → 已复制 markdown: {dest_md.name}")

    # 生成 HTML
    render_meta = {**meta}
    render_meta["date"] = entry.get("date") or meta.get("date", date_str)

    links = {
        "dateLink": entry.get("dateLink", ""),
        "categoryLink": entry.get("categoryLink", ""),
        "link": entry.get("link", ""),
        "imageLink": entry.get("imageLink", ""),
    }

    body_html = markdown.markdown(
        body, extensions=["fenced_code", "tables"]
    )
    body_html = _style_content(body_html)
    html_content = fill_template(template, title, render_meta, body_html,
                                 archive_dir, links)

    dest_html = archive_dir / f"{entry_id}.html"
    with open(dest_html, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"      → 已生成 HTML: {dest_html.name} ({len(html_content)} 字节)")

    return "success"
