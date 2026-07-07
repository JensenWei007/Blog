// load_archive_year.js
// 年份归档页面：显示该年的所有月份及文章数
async function loadArchiveYear() {
    const container = document.getElementById('archive-year-container');
    if (!container) {
        console.error('loadArchiveYear: 找不到archive-year容器');
        return;
    }

    try {
        const response = await fetch('year.json');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();

        if (data.months && data.months.length > 0) {
            container.innerHTML = generateArchiveYearHTML(data);
        } else {
            container.innerHTML = '<p class="text-white text-center py-5">该年暂无文章</p>';
        }
    } catch (err) {
        console.error('loadArchiveYear:', err);
        container.innerHTML = '<p class="text-white text-center py-5">加载归档失败</p>';
    }
}

function generateArchiveYearHTML(data) {
    const months = [...data.months].sort((a, b) => b.month - a.month);
    const year = data.year;

    const monthNames = ['一月', '二月', '三月', '四月', '五月', '六月',
                        '七月', '八月', '九月', '十月', '十一月', '十二月'];

    return `
        <div class="mb-4">
            <a href="../archive.html" class="text-primary" style="font-size:0.9rem;">
                ← 返回归档首页
            </a>
        </div>
        ${months.map(m => {
            return `
                <div class="archive-month-item bg-dark rounded p-4 mb-3 d-flex justify-content-between align-items-center">
                    <div>
                        <h3 class="text-white mb-1">
                            <a href="${m.month}/${year}-${m.month}.html" class="text-white opacity-75-onHover">
                                ${monthNames[m.month - 1]}
                            </a>
                        </h3>
                        <span class="text-muted" style="font-size:0.85rem;">
                            ${m.post_count} 篇文章
                        </span>
                    </div>
                    <a href="${m.month}/${year}-${m.month}.html" class="btn btn-primary btn-sm">
                        查看 <img src="${(window.BLOG_BASE || '') + 'images/arrow-right.png'}" alt="" style="width:12px;">
                    </a>
                </div>
            `;
        }).join('')}
    `;
}

document.addEventListener('DOMContentLoaded', loadArchiveYear);
if (document.readyState !== 'loading') loadArchiveYear();
