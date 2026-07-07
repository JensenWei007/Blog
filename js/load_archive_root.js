// load_archive_root.js
// 归档根页面：显示所有年份及月份概览
async function loadArchiveRoot() {
    const container = document.getElementById('archive-root-container');
    if (!container) {
        console.error('loadArchiveRoot: 找不到archive-root容器');
        return;
    }

    try {
        const response = await fetch('archive.json');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();

        if (data.years && data.years.length > 0) {
            container.innerHTML = generateArchiveRootHTML(data);
        } else {
            container.innerHTML = '<p class="text-white text-center py-5">暂无归档内容</p>';
        }
    } catch (err) {
        console.error('loadArchiveRoot:', err);
        container.innerHTML = '<p class="text-white text-center py-5">加载归档失败</p>';
    }
}

function generateArchiveRootHTML(data) {
    // 按年份倒序
    const years = [...data.years].sort((a, b) => b.year - a.year);

    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

    return years.map(yearData => {
        const months = [...yearData.months].sort((a, b) => b - a);
        const monthBadges = months.map(m => {
            return `<a href="${yearData.year}/${m}/${yearData.year}-${m}.html"
                        class="badge badge-pill bg-dark text-white mr-2 mb-2 px-3 py-2"
                        style="font-size:0.9rem; border:1px solid #444;">
                        ${monthNames[m - 1]}
                    </a>`;
        }).join('');

        return `
            <div class="archive-year-block mb-5">
                <h2 class="text-white add-letter-space mb-3">
                    <a href="${yearData.year}/${yearData.year}.html" class="text-white opacity-75-onHover">
                        ${yearData.year}
                    </a>
                    <span class="text-muted ml-3" style="font-size:0.8rem;">
                        ${yearData.post_count} 篇文章
                    </span>
                </h2>
                <div class="d-flex flex-wrap">${monthBadges}</div>
            </div>
        `;
    }).join('');
}

document.addEventListener('DOMContentLoaded', loadArchiveRoot);
if (document.readyState !== 'loading') loadArchiveRoot();
