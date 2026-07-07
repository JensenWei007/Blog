// load_category_detail.js
// 单个分类页面：显示该分类下所有文章（卡片布局）
// BLOG_BASE 由 HTML 页面注入，指向 Blog 根目录
async function loadCategoryDetail() {
    const container = document.getElementById('category-detail-container');
    if (!container) {
        console.error('loadCategoryDetail: 找不到category-detail容器');
        return;
    }

    // 从当前 HTML 文件名推断分类 ID（如 0.html → 0）
    const pageName = window.location.pathname.split('/').pop().replace('.html', '');
    const jsonPath = pageName + '.json';

    try {
        const response = await fetch(jsonPath);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const posts = await response.json();

        if (posts && posts.length > 0) {
            container.innerHTML = generatePostCards(posts);
        } else {
            container.innerHTML = '<p class="text-white text-center py-5">该分类暂无文章</p>';
        }
    } catch (err) {
        console.error('loadCategoryDetail:', err);
        container.innerHTML = '<p class="text-white text-center py-5">加载文章失败</p>';
    }
}

function resolveAsset(path) {
    if (!path) return '';
    if (/^(https?:|\/\/|data:)/.test(path)) return path;
    return (window.BLOG_BASE || '') + path;
}

function generatePostCards(posts) {
    return posts.map(post => `
        <div class="index post-item bg-transparent border-0 mb-5">
            ${post.image ? `
            <a href="${post.link || '#'}">
                <img class="card-img-top rounded-0" src="${resolveAsset(post.image)}" alt="${post.imageAlt || post.title}">
            </a>
            ` : ''}

            <div class="index-body px-0">
                <h2 class="index-title">
                    <a class="text-white opacity-75-onHover" href="${post.link || '#'}">${post.title}</a>
                </h2>

                ${post.date || post.category ? `
                <ul class="post-meta mt-3">
                    ${post.date ? `
                    <li class="d-inline-block mr-3">
                        <span class="fas fa-clock text-primary"></span>
                        <a class="ml-1" href="${post.dateLink || '#'}">${post.date}</a>
                    </li>
                    ` : ''}
                    ${post.category ? `
                    <li class="d-inline-block">
                        <span class="fas fa-list-alt text-primary"></span>
                        <a class="ml-1" href="${post.categoryLink || '#'}">${post.category}</a>
                    </li>
                    ` : ''}
                </ul>
                ` : ''}

                ${post.description ? `
                <p class="index-text my-4">${post.description}</p>
                ` : ''}

                <a href="${post.link || '#'}" class="btn btn-primary">
                    Read More <img src="${resolveAsset('images/arrow-right.png')}" alt="">
                </a>
            </div>
        </div>
    `).join('');
}

document.addEventListener('DOMContentLoaded', loadCategoryDetail);
if (document.readyState !== 'loading') loadCategoryDetail();
