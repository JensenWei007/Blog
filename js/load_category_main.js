// load_category_main.js
// 分类主页面：显示所有分类及文章数
async function loadCategoryMain() {
    const container = document.getElementById('category-main-container');
    if (!container) {
        console.error('loadCategoryMain: 找不到category-main容器');
        return;
    }

    try {
        const response = await fetch('json/category.json');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const categories = await response.json();

        if (categories && categories.length > 0) {
            container.innerHTML = generateCategoryMainHTML(categories);
        } else {
            container.innerHTML = '<p class="text-white text-center py-5">暂无分类</p>';
        }
    } catch (err) {
        console.error('loadCategoryMain:', err);
        container.innerHTML = '<p class="text-white text-center py-5">加载分类失败</p>';
    }
}

function generateCategoryMainHTML(categories) {
    // 按文章数降序
    const sorted = [...categories].sort((a, b) => b.post_count - a.post_count);

    return sorted.map(cat => `
        <div class="archive-month-item bg-dark rounded p-4 mb-3 d-flex justify-content-between align-items-center">
            <div>
                <h3 class="text-white mb-1">
                    <a href="category/${cat.id}.html" class="text-white opacity-75-onHover">
                        ${cat.name}
                    </a>
                </h3>
                <span class="text-muted" style="font-size:0.85rem;">
                    ${cat.post_count} 篇文章
                </span>
            </div>
            <a href="category/${cat.id}.html" class="btn btn-primary btn-sm">
                查看 <img src="images/arrow-right.png" alt="" style="width:12px;">
            </a>
        </div>
    `).join('');
}

document.addEventListener('DOMContentLoaded', loadCategoryMain);
if (document.readyState !== 'loading') loadCategoryMain();
