// load-post.js
async function loadPost() {
    const postContainer = document.getElementById('post-container');

    if (!postContainer) {
        console.error('loadPost: 找不到post容器元素');
        return;
    }

    const response = await fetch('./json/post.json');

    if (!response.ok) {
        throw new Error(`loadPost: HTTP错误! 状态码: ${response.status}`);
    }

    const posts = await response.json();

    if (posts && posts.length > 0) {
        postContainer.innerHTML = generatePostHTML(posts);
    } else {
        postContainer.innerHTML = '<p class="text-white">暂无内容</p>';
    }
}

function generatePostHTML(posts) {
    return posts.map(post => `
        <div class="post post-item bg-transparent border-0 mb-5">
            ${post.image ? `
            <!-- 图片部分 - 可选 -->
            <a href="${post.imageLink || post.link || 'to.html'}">
                <img class="card-img-top rounded-0" src="${post.image}" alt="${post.imageAlt || post.title}">
            </a>
            ` : ''}
            
            <!-- 文字部分 -->
            <div class="card-body px-0">
                <!-- 大标题 -->
                <h2 class="card-title">
                    <a class="text-white opacity-75-onHover" href="${post.link || 'post-details.html'}">${post.title}</a>
                </h2>

                <!-- 发布时间和分类 - 可选 -->
                ${post.date || post.category ? `
                <ul class="post-meta mt-3 mb-4">
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
                
                <!-- 跳转按钮 -->
                <a href="${post.link || 'post-details.html'}" class="btn btn-primary">Read More <img src="images/arrow-right.png" alt=""></a>
            </div>
        </div>
    `).join('');
}

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', loadPost);

// 备用加载方式：如果DOMContentLoaded已经触发
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadPost);
} else {
    // DOMContentLoaded 已经触发，直接执行
    loadPost();
}