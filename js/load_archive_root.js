// load_archive_root.js
// 归档根页面：以圆角矩形卡片显示各年份及月份
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
    const years = [...data.years].sort((a, b) => b.year - a.year);

    const monthNames = ['一月', '二月', '三月', '四月', '五月', '六月',
                        '七月', '八月', '九月', '十月', '十一月', '十二月'];

    return years.map(yearData => {
        const months = [...yearData.months].sort((a, b) => b.month - a.month);
        const monthBlocks = months.map(m => `
            <a href="${yearData.year}/${m.month}/${yearData.year}-${m.month}.html"
               style="display:inline-block; background:#2a2930; color:#ccc;
                      padding:10px 22px; margin:5px 8px 5px 0;
                      border-radius:8px; font-size:1.05rem;
                      text-decoration:none; transition:all 0.2s;"
               onmouseover="this.style.background='#E4112F';this.style.color='#fff'"
               onmouseout="this.style.background='#2a2930';this.style.color='#ccc'">
                ${monthNames[m.month - 1]}
            </a>
        `).join('');

        return `
            <div style="background:#1D1C21; border-radius:16px; padding:24px 28px; margin-bottom:24px;">
                <h1 class="text-white add-letter-space" style="margin:0 0 18px 0;">
                    <a href="${yearData.year}/${yearData.year}.html"
                       style="color:#fff; text-decoration:none;"
                       onmouseover="this.style.color='#E4112F'"
                       onmouseout="this.style.color='#fff'">
                        ${yearData.year}
                    </a>
                </h1>
                <div style="line-height:1.8;">${monthBlocks}</div>
            </div>
        `;
    }).join('');
}

document.addEventListener('DOMContentLoaded', loadArchiveRoot);
if (document.readyState !== 'loading') loadArchiveRoot();
