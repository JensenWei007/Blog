// load-index.js
async function loadIndex() {
    const indexContainer = document.getElementById('index-container');

    if (!indexContainer) {
        console.error('loadIndex: 找不到index容器元素');
        return;
    }

    const response = await fetch('./json/index.json');

    if (!response.ok) {
        throw new Error(`loadIndex: HTTP错误! 状态码: ${response.status}`);
    }

    const indexs = await response.json();

    if (indexs && indexs.length > 0) {
        indexContainer.innerHTML = generateIndexHTML(indexs);
    } else {
        indexContainer.innerHTML = '<p class="text-white">暂无内容</p>';
    }
}

function generateIndexHTML(indexs) {
    return indexs.map(index => `
        <div class="index post-item bg-transparent border-0 mb-5">
            ${index.image ? `
            <!-- 图片部分 - 可选 -->
            <a href="${index.imageLink || index.link || 'to.html'}">
                <img class="card-img-top rounded-0" src="${index.image}" alt="${index.imageAlt || index.title}">
            </a>
            ` : ''}
            
            <!-- 文字部分 -->
            <div class="index-body px-0">
                <!-- 大标题 -->
                <h2 class="index-title">
                    <a class="text-white opacity-75-onHover" href="${index.link || 'post-details.html'}">${index.title}</a>
                </h2>

                <!-- 发布时间和分类 - 可选 -->
                ${index.date || index.category ? `
                <ul class="post-meta mt-3">
                    ${index.date ? `
                    <li class="d-inline-block mr-3">
                        <span class="fas fa-clock text-primary"></span>
                        <a class="ml-1" href="${index.dateLink || '#'}">${index.date}</a>
                    </li>
                    ` : ''}
                    ${index.category ? `
                    <li class="d-inline-block">
                        <span class="fas fa-list-alt text-primary"></span>
                        <a class="ml-1" href="${index.categoryLink || '#'}">${index.category}</a>
                    </li>
                    ` : ''}
                </ul>
                ` : ''}

                <!-- 详细介绍文本 - 可选 -->
                ${index.description ? `
                <p class="index-text my-4">${index.description}</p>
                ` : ''}
                
                <!-- 跳转按钮 -->
                <a href="${index.link || 'post-details.html'}" class="btn btn-primary">Read More <img src="images/arrow-right.png" alt=""></a>
            </div>
        </div>
    `).join('');
}

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', loadIndex);

// 备用加载方式：如果DOMContentLoaded已经触发
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadIndex);
} else {
    // DOMContentLoaded 已经触发，直接执行
    loadIndex();
}