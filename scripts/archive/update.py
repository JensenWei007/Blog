"""更新模式：扫描 all.json 重新生成 HTML，重建全部索引。"""

from .alljson import load_all_json, save_all_json, build_cat_id_map
from .entry import process_entry, compute_entry_links
from .archive_index import build_archive_index, write_archive_json_files, ensure_archive_pages
from .category_index import build_category_index, write_category_files, ensure_category_pages


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
