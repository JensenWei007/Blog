"""分类索引构建、JSON 写入、HTML 页面生成。"""

import json

from .config import BLOG_ROOT, CATEGORY_ROOT, CATEGORY_DETAIL_CONTENT
from .frontmatter import parse_front_matter, parse_date_to_archive_path
from .template import fill_archive_page


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
            "categoryLink": "",
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
