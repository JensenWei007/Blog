#!/usr/bin/env python3
"""
generate_archive.py

Blog 静态站点生成器。以 all.json 为唯一真索引。

用法：
    # 新增文章 —— 解析 .md 文件，自动分配 id，加入 all.json，生成归档
    python3 scripts/generate_archive.py new_post.md
    python3 scripts/generate_archive.py --dry-run new_post.md

    # 更新模式 —— 扫描 all.json 全部条目，重新生成 HTML（模板修改后使用）
    python3 scripts/generate_archive.py
    python3 scripts/generate_archive.py --dry-run
    python3 scripts/generate_archive.py --id 2           # 仅更新指定条目
"""

import json
import os
import sys
import argparse
import shutil
import re
from datetime import datetime
from pathlib import Path

import markdown


# --- 配置 ---
BLOG_ROOT = Path(__file__).resolve().parent.parent  # ~/Blog
ALL_JSON = BLOG_ROOT / "all.json"
ARCHIVE_ROOT = BLOG_ROOT / "archive"
CATEGORY_ROOT = BLOG_ROOT / "category"
MD_DIR = BLOG_ROOT / "md"
TEMPLATE_PATH = BLOG_ROOT / "template.html"


# ======================================================================
#  Front Matter 解析
# ======================================================================

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


# ======================================================================
#  日期解析
# ======================================================================

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


# ======================================================================
#  all.json 读写
# ======================================================================

def load_all_json() -> list:
    """读取 all.json，返回条目列表。"""
    if not ALL_JSON.is_file():
        raise FileNotFoundError(f"找不到 {ALL_JSON}")
    with open(ALL_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("all.json 应该是一个 JSON 数组")
    return data


def save_all_json(entries: list) -> None:
    """写入 all.json。"""
    with open(ALL_JSON, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


def next_id(entries: list) -> int:
    """返回下一个可用 id（max id + 1，没有条目时从 0 开始）。"""
    if not entries:
        return 0
    return max(e.get("id", -1) for e in entries) + 1


# ======================================================================
#  模板处理
# ======================================================================

def load_template() -> str:
    """读取 template.html。"""
    if not TEMPLATE_PATH.is_file():
        raise FileNotFoundError(f"模板文件不存在: {TEMPLATE_PATH}")
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        return f.read()


def build_image_block(meta: dict, links: dict) -> str:
    """构建题图 <img>（可点击跳转到文章）。无图返回空字符串。"""
    image = meta.get("image", "").strip()
    if not image:
        return ""
    alt = meta.get("imageAlt", meta.get("title", "")).strip()
    img_html = f'<img class="img-fluid" src="{image}" alt="{alt}">'
    image_link = links.get("imageLink") or links.get("link", "")
    if image_link:
        return f'<a href="{image_link}">{img_html}</a>'
    return img_html


def build_meta_block(meta: dict, links: dict) -> str:
    """构建日期+分类的 <ul>，点击可跳转到归档月页/分类页。无信息返回空字符串。"""
    date_display = meta.get("date", "").strip()
    category = meta.get("category", "").strip()
    if not date_display and not category:
        return ""
    parts = []
    if date_display:
        date_link = links.get("dateLink", "#")
        parts.append(
            '<li class="d-inline-block mr-3">'
            '<span class="fas fa-clock text-primary"></span>'
            f'<a class="ml-1" href="{date_link}">{date_display}</a>'
            '</li>'
        )
    if category:
        cat_link = links.get("categoryLink", "#")
        parts.append(
            '<li class="d-inline-block">'
            '<span class="fas fa-list-alt text-primary"></span>'
            f'<a class="ml-1" href="{cat_link}">{category}</a>'
            '</li>'
        )
    return f'<ul class="post-meta mt-3 mb-4">{"".join(parts)}</ul>'


def adjust_resource_paths(html: str, output_dir: Path) -> str:
    """将模板中相对于 Blog 根的 src/href 调整为从 output_dir 可访问的路径。"""
    base_path = os.path.relpath(BLOG_ROOT, output_dir)

    def _replace(match: re.Match) -> str:
        attr = match.group(1)
        quote = match.group(2)
        url = match.group(3)
        if (not url or
            url.startswith("http://") or url.startswith("https://") or
            url.startswith("//") or url.startswith("#") or
            url.startswith("data:") or url.startswith("../") or
            url.startswith("{{")):
            return match.group(0)
        clean_url = url.lstrip("./")
        return f'{attr}={quote}{base_path}/{clean_url}{quote}'

    return re.sub(r'(src|href)=("|\')(.*?)\2', _replace, html, flags=re.IGNORECASE)


def fill_template(template: str, title: str, meta: dict, body_html: str,
                  output_dir: Path, links: dict = None) -> str:
    """用文章数据填充模板并调整资源路径。links 包含 dateLink/categoryLink/imageLink。"""
    if links is None:
        links = {}
    html = template.replace("{{ title }}", title)
    html = html.replace("{{ image_block }}", build_image_block(meta, links))
    html = html.replace("{{ meta_block }}", build_meta_block(meta, links))
    html = html.replace("{{ content }}", body_html)
    return adjust_resource_paths(html, output_dir)


def fill_archive_page(template: str, title: str, content_html: str,
                      output_dir: Path) -> str:
    """用归档/分类页面数据填充模板。"""
    base_path = os.path.relpath(BLOG_ROOT, output_dir)
    content_html = content_html.replace("{{ base_path }}", base_path)
    html = template.replace("{{ title }}", title)
    html = html.replace("{{ image_block }}", "")
    html = html.replace("{{ meta_block }}", "")
    html = html.replace("{{ content }}", content_html)
    return adjust_resource_paths(html, output_dir)


# ======================================================================
#  文章处理（单篇生成）
# ======================================================================

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
        # 回退：md/{id}.md
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
    # 优先使用 all.json 中的显示日期，其次用 front matter 的日期
    render_meta["date"] = entry.get("date") or meta.get("date", date_str)

    # 提取链接字段
    links = {
        "dateLink": entry.get("dateLink", ""),
        "categoryLink": entry.get("categoryLink", ""),
        "link": entry.get("link", ""),
        "imageLink": entry.get("imageLink", ""),
    }

    body_html = markdown.markdown(
        body, extensions=["fenced_code", "codehilite", "tables", "toc"]
    )
    html_content = fill_template(template, title, render_meta, body_html,
                                 archive_dir, links)

    dest_html = archive_dir / f"{entry_id}.html"
    with open(dest_html, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"      → 已生成 HTML: {dest_html.name} ({len(html_content)} 字节)")

    return "success"


def compute_entry_links(entry: dict, cat_id_map: dict) -> None:
    """根据条目的日期和分类，自动设置 link / dateLink / categoryLink / imageLink。"""
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


def build_cat_id_map(entries: list) -> dict:
    """从 all.json 条目中提取 {category_name: category_id} 映射。"""
    cats = sorted(set(
        e.get("category", "") for e in entries
        if e.get("category") and e.get("source")
    ))
    return {name: idx for idx, name in enumerate(cats)}


# ======================================================================
#  新文章摄入
# ======================================================================

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

    # 写入 md 目录
    MD_DIR.mkdir(parents=True, exist_ok=True)
    dest_md = MD_DIR / f"{new_id}.md"
    if not dry_run:
        shutil.copy2(md_path, dest_md)
        print(f"  ✓ 已复制: {md_path.name} → {dest_md}")

    # 解析日期
    date_str = meta.get("date", datetime.now().strftime("%Y-%m-%d"))
    try:
        year, month, day = parse_date_to_archive_path(date_str)
    except ValueError:
        year, month, day = datetime.now().year, datetime.now().month, datetime.now().day

    try:
        display_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%-d %B, %Y")
    except ValueError:
        display_date = date_str

    # 计算分类 id（基于已有条目 + 新条目可能引入的新分类）
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

    # 自动计算 link 字段
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


# ======================================================================
#  归档索引
# ======================================================================

def build_archive_index(all_entries: list, cat_id_map: dict = None) -> dict:
    """按年→月聚合文章数据。cat_id_map 为 {category_name: id} 映射。"""
    if cat_id_map is None:
        cat_id_map = build_cat_id_map(all_entries)
    years_map: dict = {}
    for entry in all_entries:
        source_file = entry.get("source") or entry.get("md_file")
        if not source_file:
            continue
        md_path = BLOG_ROOT / source_file
        if not md_path.is_file():
            continue
        meta, _body = parse_front_matter(md_path)
        date_str = meta.get("date") or entry.get("date", "")
        try:
            year, month, day = parse_date_to_archive_path(date_str)
        except ValueError:
            continue
        display_date = entry.get("date", date_str)
        cat_id = cat_id_map.get(meta.get("category") or entry.get("category", ""), 0)
        post_entry = {
            "id": entry.get("id"),
            "title": meta.get("title") or entry.get("title", "未命名"),
            "date": display_date,
            "dateLink": f"{year}-{month}.html",
            "category": meta.get("category") or entry.get("category", ""),
            "categoryLink": f"../../../category/{cat_id}.html",
            "description": meta.get("description") or entry.get("description", ""),
            "link": f"{day}/{entry['id']}/{entry['id']}.html",
            "image": meta.get("image") or entry.get("image", ""),
            "imageAlt": meta.get("imageAlt") or entry.get("imageAlt", ""),
        }
        years_map.setdefault(year, {}).setdefault(month, []).append(post_entry)

    years_list = []
    for year in sorted(years_map.keys(), reverse=True):
        months_data = years_map[year]
        months_list = []
        total = 0
        for month in sorted(months_data.keys(), reverse=True):
            posts = months_data[month]
            months_list.append({"month": month, "post_count": len(posts)})
            total += len(posts)
        years_list.append({"year": year, "months": months_list, "post_count": total})

    return {
        "years": years_list,
        "total_posts": sum(y["post_count"] for y in years_list),
        "years_map": years_map,
    }


def write_archive_json_files(archive_data: dict) -> None:
    """写入 archive.json / year.json / month.json。"""
    root_json = {"years": archive_data["years"], "total_posts": archive_data["total_posts"]}
    (ARCHIVE_ROOT / "archive.json").parent.mkdir(parents=True, exist_ok=True)
    with open(ARCHIVE_ROOT / "archive.json", "w", encoding="utf-8") as f:
        json.dump(root_json, f, ensure_ascii=False, indent=2)
    print(f"  ✓ 归档索引: archive/archive.json")

    years_map = archive_data.get("years_map", {})
    for year, months_data in years_map.items():
        year_dir = ARCHIVE_ROOT / str(year)
        months_list = []
        for month in sorted(months_data.keys(), reverse=True):
            posts = months_data[month]
            months_list.append({"month": month, "post_count": len(posts)})
        year_total = sum(m["post_count"] for m in months_list)
        year_dir.mkdir(parents=True, exist_ok=True)
        with open(year_dir / "year.json", "w", encoding="utf-8") as f:
            json.dump({"year": year, "months": months_list, "post_count": year_total},
                      f, ensure_ascii=False, indent=2)
        print(f"  ✓ 年份索引: archive/{year}/year.json")

        for month, posts in months_data.items():
            month_dir = year_dir / str(month)
            month_dir.mkdir(parents=True, exist_ok=True)
            with open(month_dir / "month.json", "w", encoding="utf-8") as f:
                json.dump(posts, f, ensure_ascii=False, indent=2)
            print(f"  ✓ 月份索引: archive/{year}/{month}/month.json")


# 归档页面内容片段
ARCHIVE_ROOT_CONTENT = """\
<script>var BLOG_BASE = "{{ base_path }}";</script>
<div id="archive-root-container">
    <div class="text-center text-white py-5">
        <div class="spinner-border text-primary" role="status"><span class="sr-only">Loading...</span></div>
        <p class="mt-3">正在加载归档...</p>
    </div>
</div>
<script src="js/load_archive_root.js"></script>"""

ARCHIVE_YEAR_CONTENT = """\
<script>var BLOG_BASE = "{{ base_path }}";</script>
<div id="archive-year-container">
    <div class="text-center text-white py-5">
        <div class="spinner-border text-primary" role="status"><span class="sr-only">Loading...</span></div>
        <p class="mt-3">正在加载归档...</p>
    </div>
</div>
<script src="js/load_archive_year.js"></script>"""

ARCHIVE_MONTH_CONTENT = """\
<script>var BLOG_BASE = "{{ base_path }}";</script>
<div id="archive-month-container">
    <div class="text-center text-white py-5">
        <div class="spinner-border text-primary" role="status"><span class="sr-only">Loading...</span></div>
        <p class="mt-3">正在加载文章列表...</p>
    </div>
</div>
<script src="js/load_archive_month.js"></script>"""


def ensure_archive_pages(template: str, archive_data: dict) -> None:
    """生成各层级归档 HTML 页面（已存在则跳过）。"""
    root_page = ARCHIVE_ROOT / "archive.html"
    if not root_page.is_file():
        html = fill_archive_page(template, "文章归档", ARCHIVE_ROOT_CONTENT, ARCHIVE_ROOT)
        root_page.parent.mkdir(parents=True, exist_ok=True)
        with open(root_page, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  ✓ 归档首页: {root_page}")

    years_map = archive_data.get("years_map", {})
    for year, months_data in years_map.items():
        year_dir = ARCHIVE_ROOT / str(year)
        year_page = year_dir / f"{year}.html"
        if not year_page.is_file():
            html = fill_archive_page(template, f"{year}年", ARCHIVE_YEAR_CONTENT, year_dir)
            year_dir.mkdir(parents=True, exist_ok=True)
            with open(year_page, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"  ✓ 年份归档页: {year_page}")

        for month in months_data.keys():
            month_dir = year_dir / str(month)
            month_page = month_dir / f"{year}-{month}.html"
            if not month_page.is_file():
                html = fill_archive_page(template, f"{year}年{month}月",
                                         ARCHIVE_MONTH_CONTENT, month_dir)
                month_dir.mkdir(parents=True, exist_ok=True)
                with open(month_page, "w", encoding="utf-8") as f:
                    f.write(html)
                print(f"  ✓ 月份归档页: {month_page}")


# ======================================================================
#  分类索引
# ======================================================================

CATEGORY_DETAIL_CONTENT = """\
<script>var BLOG_BASE = "{{ base_path }}";</script>
<div class="mb-4">
    <a href="../category.html" class="text-primary" style="font-size:0.9rem;">← 返回分类列表</a>
</div>
<div id="category-detail-container">
    <div class="text-center text-white py-5">
        <div class="spinner-border text-primary" role="status"><span class="sr-only">Loading...</span></div>
        <p class="mt-3">正在加载文章列表...</p>
    </div>
</div>
<script src="js/load_category_detail.js"></script>"""


def build_category_index(all_entries: list) -> dict:
    """按分类聚合文章，为每个分类分配 ID。"""
    cat_map: dict = {}
    for entry in all_entries:
        source_file = entry.get("source") or entry.get("md_file")
        if not source_file:
            continue
        md_path = BLOG_ROOT / source_file
        if not md_path.is_file():
            continue
        meta, _body = parse_front_matter(md_path)
        date_str = meta.get("date") or entry.get("date", "")
        try:
            year, month, day = parse_date_to_archive_path(date_str)
        except ValueError:
            continue
        category = meta.get("category") or entry.get("category", "")
        if not category:
            category = "未分类"
        display_date = entry.get("date", date_str)
        post_entry = {
            "id": entry.get("id"),
            "title": meta.get("title") or entry.get("title", "未命名"),
            "date": display_date,
            "dateLink": f"../archive/{year}/{month}/{year}-{month}.html",
            "category": category,
            "categoryLink": "",  # 稍后填入
            "description": meta.get("description") or entry.get("description", ""),
            "link": f"../archive/{year}/{month}/{day}/{entry['id']}/{entry['id']}.html",
            "image": meta.get("image") or entry.get("image", ""),
            "imageAlt": meta.get("imageAlt") or entry.get("imageAlt", ""),
        }
        cat_map.setdefault(category, []).append(post_entry)

    cat_list = []
    cat_id_map = {}
    for idx, (cat_name, posts) in enumerate(sorted(cat_map.items())):
        cat_list.append({"id": idx, "name": cat_name, "post_count": len(posts),
                         "link": f"category/{idx}.html"})
        cat_id_map[cat_name] = idx
        # 回填 categoryLink
        for p in posts:
            p["categoryLink"] = f"{idx}.html"

    return {"categories": cat_list, "cat_map": cat_map, "cat_id_map": cat_id_map}


def write_category_files(category_data: dict) -> None:
    """写入 json/category.json 和 category/{id}.json。"""
    cat_index_path = BLOG_ROOT / "json" / "category.json"
    cat_index_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cat_index_path, "w", encoding="utf-8") as f:
        json.dump(category_data["categories"], f, ensure_ascii=False, indent=2)
    print(f"  ✓ 分类索引: json/category.json")

    cat_map = category_data.get("cat_map", {})
    cat_id_map = category_data.get("cat_id_map", {})
    CATEGORY_ROOT.mkdir(parents=True, exist_ok=True)
    for cat_name, posts in cat_map.items():
        cat_id = cat_id_map[cat_name]
        with open(CATEGORY_ROOT / f"{cat_id}.json", "w", encoding="utf-8") as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
        print(f"  ✓ 分类 [{cat_name}] JSON: category/{cat_id}.json")


def ensure_category_pages(template: str, category_data: dict) -> None:
    """生成分类详情 HTML 页面（已存在则跳过）。"""
    cat_id_map = category_data.get("cat_id_map", {})
    CATEGORY_ROOT.mkdir(parents=True, exist_ok=True)
    for cat_name, cat_id in cat_id_map.items():
        cat_page = CATEGORY_ROOT / f"{cat_id}.html"
        if not cat_page.is_file():
            html = fill_archive_page(template, f"{cat_name}",
                                     CATEGORY_DETAIL_CONTENT, CATEGORY_ROOT)
            with open(cat_page, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"  ✓ 分类页: category/{cat_id}.html")


def sync_all_entry_links(all_entries: list) -> bool:
    """为所有条目补全 link / dateLink / categoryLink 字段，如有变更则写回 all.json。"""
    cat_id_map = build_cat_id_map(all_entries)
    changed = False
    for entry in all_entries:
        if not entry.get("source"):
            continue
        old_link = entry.get("link", "")
        old_date = entry.get("dateLink", "")
        old_cat = entry.get("categoryLink", "")
        compute_entry_links(entry, cat_id_map)
        if (entry.get("link") != old_link or
            entry.get("dateLink") != old_date or
            entry.get("categoryLink") != old_cat):
            changed = True
    if changed:
        save_all_json(all_entries)
        print("  ✓ all.json 链接字段已更新")
    return changed


def rebuild_indexes(template: str, all_entries: list) -> None:
    """重建归档和分类的全部 JSON 及 HTML 页面。"""
    # 先同步 link 字段
    sync_all_entry_links(all_entries)

    print("\n📊 重建归档索引...")
    cat_id_map = build_cat_id_map(all_entries)
    archive_data = build_archive_index(all_entries, cat_id_map)
    write_archive_json_files(archive_data)
    print("\n📄 检查归档页面...")
    ensure_archive_pages(template, archive_data)

    print("\n📊 重建分类索引...")
    category_data = build_category_index(all_entries)
    write_category_files(category_data)
    print("\n📄 检查分类页面...")
    ensure_category_pages(template, category_data)


# ======================================================================
#  更新模式 —— 扫描 all.json 重新生成 HTML
# ======================================================================

def update_all(template: str, dry_run: bool = False,
               target_id: int = None) -> tuple[int, int, int]:
    """
    扫描 all.json 全部条目，重新生成 HTML。
    如果指定 target_id，则只更新该条目。
    返回 (success, skip, fail) 计数。
    """
    all_entries = load_all_json()
    success = skip = fail = 0

    for entry in all_entries:
        entry_id = entry.get("id")
        if target_id is not None and entry_id != target_id:
            continue
        print(f"── 更新 id={entry_id}: {entry.get('title', '无标题')}")
        result = process_entry(entry, template, dry_run=dry_run)
        if result == "success":
            success += 1
        elif result == "skip":
            skip += 1
        else:
            fail += 1

    if not dry_run and (target_id is None or success > 0):
        rebuild_indexes(template, load_all_json())

    return success, skip, fail


# ======================================================================
#  主入口
# ======================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Blog 静态站点生成器 —— 以 all.json 为唯一真索引")
    parser.add_argument("new_md", nargs="?", default=None,
                        help="新文章的 .md 文件路径（新增模式）")
    parser.add_argument("--dry-run", action="store_true",
                        help="仅预览，不做实际修改")
    parser.add_argument("--id", type=int, default=None,
                        help="更新模式下仅处理指定 id 的条目")
    args = parser.parse_args()

    # 检查模板
    if not TEMPLATE_PATH.is_file():
        print(f"✗ 错误：模板文件不存在: {TEMPLATE_PATH}")
        sys.exit(1)

    try:
        template = load_template()
    except Exception as e:
        print(f"✗ 错误：读取模板失败: {e}")
        sys.exit(1)

    if not args.dry_run:
        ARCHIVE_ROOT.mkdir(parents=True, exist_ok=True)
        MD_DIR.mkdir(parents=True, exist_ok=True)
        CATEGORY_ROOT.mkdir(parents=True, exist_ok=True)

    # ── 新增模式 ──
    if args.new_md:
        print(f"📝 新增模式：摄入 {args.new_md}\n")
        ok = ingest_new_post(Path(args.new_md), template, dry_run=args.dry_run)

        if not args.dry_run and ok:
            print("\n📊 重建索引...")
            rebuild_indexes(template, load_all_json())

        print(f"\n{'🏁 新增完成' if not args.dry_run else '🏁 预览完成'}")
        if args.dry_run:
            print("   (DRY-RUN 模式，未做实际修改)")
        sys.exit(0 if ok else 1)

    # ── 更新模式（默认）──
    print("🔄 更新模式：扫描 all.json 重新生成 HTML")
    print(f"📄 使用模板: {TEMPLATE_PATH.name}\n")

    success, skip, fail = update_all(template, dry_run=args.dry_run,
                                     target_id=args.id)

    total = success + skip + fail
    print(f"\n{'🏁 更新完成' if not args.dry_run else '🏁 预览完成'}")
    print(f"   成功: {success}  跳过(无源文件): {skip}  失败: {fail}")

    if args.dry_run:
        print("   (DRY-RUN 模式，未做实际修改)")

    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
