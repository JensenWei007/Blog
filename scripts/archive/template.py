"""模板加载、填充与资源路径调整。"""

import os
import re
from pathlib import Path

from .config import BLOG_ROOT, TEMPLATE_PATH


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
