"""all.json 读写与分类 ID 映射。"""

import json

from .config import ALL_JSON


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


def build_cat_id_map(entries: list) -> dict:
    """从 all.json 条目中提取 {category_name: category_id} 映射。"""
    cats = sorted(set(
        e.get("category", "") for e in entries
        if e.get("category") and e.get("source")
    ))
    return {name: idx for idx, name in enumerate(cats)}
