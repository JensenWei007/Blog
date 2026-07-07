"""全局路径与内容模板常量。"""

from pathlib import Path

# --- 路径 ---
BLOG_ROOT = Path(__file__).resolve().parent.parent.parent  # ~/Blog
ALL_JSON = BLOG_ROOT / "all.json"
ARCHIVE_ROOT = BLOG_ROOT / "archive"
CATEGORY_ROOT = BLOG_ROOT / "category"
MD_DIR = BLOG_ROOT / "md"
TEMPLATE_PATH = BLOG_ROOT / "template.html"

# --- 归档页面 JS 内容片段 ---
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
