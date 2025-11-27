// load-cards.js
async function loadCards() {
    const cardsContainer = document.getElementById('cards-container');

    if (!cardsContainer) {
        console.error('loadCards: 找不到卡片容器元素');
        return;
    }

    const response = await fetch('./json/index.json');

    if (!response.ok) {
        throw new Error(`loadCards: HTTP错误! 状态码: ${response.status}`);
    }

    const cards = await response.json();

    if (cards && cards.length > 0) {
        cardsContainer.innerHTML = generateCardsHTML(cards);
    } else {
        cardsContainer.innerHTML = '<p class="text-white">暂无内容</p>';
    }
}

function generateCardsHTML(cards) {
    return cards.map(card => `
        <div class="card post-item bg-transparent border-0 mb-5">
            ${card.image ? `
            <!-- 图片部分 - 可选 -->
            <a href="${card.imageLink || card.link || 'to.html'}">
                <img class="card-img-top rounded-0" src="${card.image}" alt="${card.imageAlt || card.title}">
            </a>
            ` : ''}
            
            <!-- 文字部分 -->
            <div class="card-body px-0">
                <!-- 大标题 -->
                <h2 class="card-title">
                    <a class="text-white opacity-75-onHover" href="${card.link || 'post-details.html'}">${card.title}</a>
                </h2>

                <!-- 发布时间和分类 - 可选 -->
                ${card.date || card.category ? `
                <ul class="post-meta mt-3">
                    ${card.date ? `
                    <li class="d-inline-block mr-3">
                        <span class="fas fa-clock text-primary"></span>
                        <a class="ml-1" href="${card.dateLink || '#'}">${card.date}</a>
                    </li>
                    ` : ''}
                    ${card.category ? `
                    <li class="d-inline-block">
                        <span class="fas fa-list-alt text-primary"></span>
                        <a class="ml-1" href="${card.categoryLink || '#'}">${card.category}</a>
                    </li>
                    ` : ''}
                </ul>
                ` : ''}

                <!-- 详细介绍文本 - 可选 -->
                ${card.description ? `
                <p class="card-text my-4">${card.description}</p>
                ` : ''}
                
                <!-- 跳转按钮 -->
                <a href="${card.link || 'post-details.html'}" class="btn btn-primary">Read More <img src="images/arrow-right.png" alt=""></a>
            </div>
        </div>
    `).join('');
}

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', loadCards);

// 备用加载方式：如果DOMContentLoaded已经触发
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadCards);
} else {
    // DOMContentLoaded 已经触发，直接执行
    loadCards();
}