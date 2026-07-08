// load_index.js
// 首页文章列表：从 json/index.json 读取 id 列表，再与 all.json 关联获取详情
async function loadIndex() {
    const container = document.getElementById('index-container');
    if (!container) {
        console.error('loadIndex: 找不到index容器元素');
        return;
    }

    try {
        const [idsResp, allResp] = await Promise.all([
            fetch('./json/index.json'),
            fetch('./all.json')
        ]);
        if (!idsResp.ok || !allResp.ok) throw new Error('HTTP error');

        const ids = await idsResp.json();
        const allEntries = await allResp.json();

        // 按 id 建立索引
        const entryMap = {};
        allEntries.forEach(e => { entryMap[e.id] = e; });

        // 按 index.json 中的顺序取出对应条目
        const posts = ids.map(id => entryMap[id]).filter(Boolean);

        container.innerHTML = posts.length
            ? generateIndexHTML(posts)
            : '<p class="text-white">暂无内容</p>';
    } catch (err) {
        console.error('loadIndex:', err);
        container.innerHTML = '<p class="text-white">加载失败</p>';
    }
}

function generateIndexHTML(posts) {
    return posts.map(post => `
        <div class="index post-item bg-transparent border-0 mb-5">
            ${post.image ? `
            <a href="${post.link || '#'}">
                <img class="card-img-top rounded-0" src="${post.image}" alt="${post.imageAlt || post.title}">
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

                <a href="${post.link || '#'}" class="btn btn-primary">Read More <img src="images/arrow-right.png" alt=""></a>
            </div>
        </div>
    `).join('');
}

document.addEventListener('DOMContentLoaded', loadIndex);
if (document.readyState !== 'loading') loadIndex();
