// load_archive_month.js
// 月份归档页面：以卡片形式显示该月所有文章（复用 index.html 的排版风格）
async function loadArchiveMonth() {
    const container = document.getElementById('archive-month-container');
    if (!container) {
        console.error('loadArchiveMonth: 找不到archive-month容器');
        return;
    }

    try {
        const response = await fetch('month.json');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const posts = await response.json();

        if (posts && posts.length > 0) {
            container.innerHTML = generatePostCards(posts);
        } else {
            container.innerHTML = '<p class="text-white text-center py-5">该月暂无文章</p>';
        }
    } catch (err) {
        console.error('loadArchiveMonth:', err);
        container.innerHTML = '<p class="text-white text-center py-5">加载文章失败</p>';
    }
}

function resolveAsset(path) {
    // 空值或已为绝对路径则直接返回，否则用 BLOG_BASE 补全
    if (!path) return '';
    if (/^(https?:|\/\/|data:)/.test(path)) return path;
    return (window.BLOG_BASE || '') + path;
}

function generatePostCards(posts) {
    // 与 index.html / load_index.js 保持一致的卡片布局
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

document.addEventListener('DOMContentLoaded', loadArchiveMonth);
if (document.readyState !== 'loading') loadArchiveMonth();
