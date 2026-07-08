// load_post.js
// 首页精选/侧边栏文章：从 json/post.json 读取 id 列表，再与 all.json 关联获取详情
async function loadPost() {
    const container = document.getElementById('post-container');
    if (!container) {
        console.error('loadPost: 找不到post容器元素');
        return;
    }

    try {
        const [idsResp, allResp] = await Promise.all([
            fetch('./json/post.json'),
            fetch('./all.json')
        ]);
        if (!idsResp.ok || !allResp.ok) throw new Error('HTTP error');

        const ids = await idsResp.json();
        const allEntries = await allResp.json();

        const entryMap = {};
        allEntries.forEach(e => { entryMap[e.id] = e; });

        const posts = ids.map(id => entryMap[id]).filter(Boolean);

        container.innerHTML = posts.length
            ? generatePostHTML(posts)
            : '<p class="text-white">暂无内容</p>';
    } catch (err) {
        console.error('loadPost:', err);
        container.innerHTML = '<p class="text-white">加载失败</p>';
    }
}

function generatePostHTML(posts) {
    return posts.map(post => `
        <div class="post post-item bg-transparent border-0 mb-5">
            ${post.image ? `
            <a href="${post.link || '#'}">
                <img class="card-img-top rounded-0" src="${post.image}" alt="${post.imageAlt || post.title}">
            </a>
            ` : ''}

            <div class="card-body px-0">
                <h2 class="card-title">
                    <a class="text-white opacity-75-onHover" href="${post.link || '#'}">${post.title}</a>
                </h2>

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

                <a href="${post.link || '#'}" class="btn btn-primary">Read More <img src="images/arrow-right.png" alt=""></a>
            </div>
        </div>
    `).join('');
}

document.addEventListener('DOMContentLoaded', loadPost);
if (document.readyState !== 'loading') loadPost();
