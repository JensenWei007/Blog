"""主入口：解析命令行参数，分发到新增/更新模式。

用法：
    python3 scripts/archive/main.py                      # 更新模式
    python3 scripts/archive/main.py new_post.md          # 新增文章
    python3 scripts/archive/main.py --dry-run            # 预览
    python3 scripts/archive/main.py --id 2               # 更新指定条目
"""

import sys
import argparse
from pathlib import Path

# 确保 Blog 根目录在 sys.path 中（支持直接 python3 scripts/archive/main.py 运行）
_BLOG_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_BLOG_ROOT) not in sys.path:
    sys.path.insert(0, str(_BLOG_ROOT))

from scripts.archive.config import ARCHIVE_ROOT, CATEGORY_ROOT, MD_DIR, TEMPLATE_PATH
from scripts.archive.template import load_template
from scripts.archive.ingest import ingest_new_post
from scripts.archive.alljson import load_all_json
from scripts.archive.update import update_all, rebuild_indexes


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
