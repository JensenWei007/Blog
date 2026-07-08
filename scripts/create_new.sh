#!/bin/bash
# create_new.sh —— 创建新文章模板
# 在 Blog/new/ 目录下生成 new.md，预填 Front Matter，date 自动取当天日期

set -e

BLOG_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NEW_DIR="$BLOG_ROOT/new"
NEW_MD="$NEW_DIR/new.md"
TODAY=$(date +%Y-%m-%d)

mkdir -p "$NEW_DIR"

if [ -f "$NEW_MD" ]; then
    echo "⚠ $NEW_MD 已存在，跳过创建"
    exit 0
fi

cat > "$NEW_MD" <<EOF
---
title:
date: $TODAY
category:
description:
---

EOF

echo "✓ 已创建: $NEW_MD"
echo "  date 已填入: $TODAY"
echo "  请编辑 title / category / description 后运行:"
echo "  python3 scripts/archive/main.py new/new.md"
