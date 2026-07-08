"""归档索引构建、JSON 写入、HTML 页面生成。"""

import json

from .config import (ARCHIVE_ROOT, BLOG_ROOT,
                     ARCHIVE_ROOT_CONTENT, ARCHIVE_YEAR_CONTENT, ARCHIVE_MONTH_CONTENT)
from .frontmatter import parse_front_matter, parse_date_to_archive_path
from .alljson import build_cat_id_map
from .template import fill_archive_page


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


def ensure_archive_pages(template: str, archive_data: dict) -> None:
    """生成各层级归档 HTML 页面（已存在则跳过）。"""
    root_page = ARCHIVE_ROOT / "archive.html"
    if not root_page.is_file():
        html = fill_archive_page(template, "Archive", ARCHIVE_ROOT_CONTENT, ARCHIVE_ROOT)
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
