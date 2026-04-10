const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const loader = document.getElementById('loader');
const splitView = document.getElementById('split-view');

let currentFilename = "";

// Support Drag & drop Native
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(e => dropZone.addEventListener(e, preventDefaults, false));
function preventDefaults(e) { e.preventDefault(); e.stopPropagation(); }
['dragenter', 'dragover'].forEach(e => dropZone.addEventListener(e, () => dropZone.classList.add('dragover'), false));
['dragleave', 'drop'].forEach(e => dropZone.addEventListener(e, () => dropZone.classList.remove('dragover'), false));

dropZone.addEventListener('drop', (e) => handleFiles(e.dataTransfer.files));
fileInput.addEventListener('change', function () { handleFiles(this.files); });

function handleFiles(files) {
    if (files.length > 0) {
        if (files[0].type !== "application/pdf") return alert("Hệ thống chỉ đọc file PDF.");
        uploadFile(files[0]);
    }
}

// Upload to Flask Server API Blueprint
function uploadFile(file) {
    currentFilename = file.name;
    dropZone.style.display = 'none';
    loader.style.display = 'block';

    let formData = new FormData();
    formData.append('pdf', file);

    fetch('/api/upload', { method: 'POST', body: formData })
        .then(res => res.json())
        .then(data => {
            loader.style.display = 'none';
            if (data.success) {
                renderUI(data.json_data);
            } else {
                dropZone.style.display = 'block';
                alert("Có lỗi trong quá trình Parser: " + data.error);
            }
        }).catch(err => {
            loader.style.display = 'none';
            dropZone.style.display = 'block';
            alert("Lỗi kết nối Backend: " + err);
        });
}

// Render cấu trúc DOM dựa trên JSON Server trả về
function renderUI(data) {
    splitView.style.display = 'grid'; // Bật Split View
    
    let pdfHtml = '';
    let jsonHtml = '[\n';

    data.forEach((page) => {
        // RENDER BÊN TRÁI (PDF)
        pdfHtml += `<div class="pdf-page" data-width="${page.width}" data-height="${page.height}">
            <img src="/api/page_image/${encodeURIComponent(currentFilename)}/${page.page_id}">`;

        // RENDER BÊN PHẢI (JSON ROOT)
        jsonHtml += `  <span class="j-toggle" onclick="toggleCollapse(this)">[-]</span><span class="j-collapsed-indicator"> {...}</span><span class="j-collapsible">{\n    <span class="j-key">"page_id"</span>: <span class="j-num">${page.page_id}</span>,\n    <span class="j-key">"width"</span>: <span class="j-num">${page.width}</span>,\n    <span class="j-key">"height"</span>: <span class="j-num">${page.height}</span>,\n    <span class="j-key">"text_blocks"</span>: <span class="j-toggle" onclick="toggleCollapse(this)">[-]</span><span class="j-collapsed-indicator"> [...]</span><span class="j-collapsible">[\n`;

        // LOOP BLOCK TEXT
        page.text_blocks.forEach((txt, idx) => {
            let bId = `page${page.page_id}-text${idx}`;
            
            let left = (txt.bbox[0] / page.width) * 100;
            let top = (txt.bbox[1] / page.height) * 100;
            let width = ((txt.bbox[2] - txt.bbox[0]) / page.width) * 100;
            let height = ((txt.bbox[3] - txt.bbox[1]) / page.height) * 100;
            
            pdfHtml += `<div class="bbox-overlay text-box" id="box-${bId}" style="left:${left}%; top:${top}%; width:${width}%; height:${height}%;" onclick="highlightUI('${bId}')" onmouseover="hoverUI('${bId}', true)" onmouseout="hoverUI('${bId}', false)"></div>`;
            
            let contentSafe = txt.content.replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\n/g, '\\n');
            jsonHtml += `<div class="json-block-node" id="json-${bId}" onclick="highlightUI('${bId}')" onmouseover="hoverUI('${bId}', true)" onmouseout="hoverUI('${bId}', false)">      {\n        <span class="j-key">"content"</span>: <span class="j-str">"${contentSafe}"</span>,\n        <span class="j-key">"bbox"</span>: [<span class="j-num">${txt.bbox.map(n => Math.round(n * 100) / 100).join(', ')}</span>]\n      }</div>${idx < page.text_blocks.length - 1 ? ',' : ''}\n`;
        });

        jsonHtml += `    ]</span>,\n    <span class="j-key">"image_blocks"</span>: <span class="j-toggle" onclick="toggleCollapse(this)">[-]</span><span class="j-collapsed-indicator"> [...]</span><span class="j-collapsible">[\n`;

        // LOOP BLOCK IMAGE 
        page.image_blocks.forEach((img, idx) => {
            let bId = `page${page.page_id}-img${idx}`;
            
            let left = (img.bbox[0] / page.width) * 100;
            let top = (img.bbox[1] / page.height) * 100;
            let width = ((img.bbox[2] - img.bbox[0]) / page.width) * 100;
            let height = ((img.bbox[3] - img.bbox[1]) / page.height) * 100;
            
            pdfHtml += `<div class="bbox-overlay img-box" id="box-${bId}" style="left:${left}%; top:${top}%; width:${width}%; height:${height}%;" onclick="highlightUI('${bId}')" onmouseover="hoverUI('${bId}', true)" onmouseout="hoverUI('${bId}', false)"></div>`;
            
            jsonHtml += `<div class="json-block-node" id="json-${bId}" onclick="highlightUI('${bId}')" onmouseover="hoverUI('${bId}', true)" onmouseout="hoverUI('${bId}', false)">      {\n        <span class="j-key">"bbox"</span>: [<span class="j-num">${img.bbox.map(n => Math.round(n * 100) / 100).join(', ')}</span>]\n      }</div>${idx < page.image_blocks.length - 1 ? ',' : ''}\n`;
        });

        pdfHtml += `</div>`;
        jsonHtml += `    ]</span>\n  }</span>${page.page_id < data.length ? ',' : ''}\n`;
    });

    jsonHtml += `]`;

    document.getElementById('pdf-render').innerHTML = pdfHtml;
    document.getElementById('json-code').innerHTML = jsonHtml;
}

let currentHighlight = null;

function highlightUI(targetId) {
    if (currentHighlight) {
        let oldBox = document.getElementById(`box-${currentHighlight}`);
        let oldJson = document.getElementById(`json-${currentHighlight}`);
        if (oldBox) oldBox.classList.remove('active-highlight');
        if (oldJson) oldJson.classList.remove('active-highlight');
    }

    let newBox = document.getElementById(`box-${targetId}`);
    let newJson = document.getElementById(`json-${targetId}`);
    
    if (newBox) {
        newBox.classList.add('active-highlight');
        let pdfPage = newBox.closest('.pdf-page');
        if (pdfPage) {
            pdfPage.scrollIntoView({ behavior: 'smooth', block: 'center' });
        } else {
            newBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    if (newJson) {
        newJson.classList.add('active-highlight');
        newJson.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    currentHighlight = targetId;
}

// Hàm hover đồng bộ 2 bên trái phải
function hoverUI(targetId, isHovering) {
    let box = document.getElementById(`box-${targetId}`);
    let jsonNode = document.getElementById(`json-${targetId}`);

    if (isHovering) {
        if (box) box.classList.add('hover-highlight');
        if (jsonNode) jsonNode.classList.add('hover-highlight');
    } else {
        if (box) box.classList.remove('hover-highlight');
        if (jsonNode) jsonNode.classList.remove('hover-highlight');
    }
}

// Logic Collapsible JSON
function toggleCollapse(btn) {
    let indicator = btn.nextElementSibling;
    let collapsable = indicator.nextElementSibling;

    if (collapsable.style.display === 'none') {
        collapsable.style.display = 'inline';
        indicator.style.display = 'none';
        btn.innerText = '[-]';
    } else {
        collapsable.style.display = 'none';
        indicator.style.display = 'inline';
        btn.innerText = '[+]';
    }
}

// Cursor coordinates tooltip binding
document.addEventListener('DOMContentLoaded', () => {
    const cursorTooltip = document.getElementById('cursor-tooltip');
    if (!cursorTooltip) return;

    document.addEventListener('mousemove', (e) => {
        const pageObj = e.target.closest('.pdf-page');
        if (pageObj) {
            cursorTooltip.style.display = 'block';
            cursorTooltip.style.left = e.clientX + 'px';
            cursorTooltip.style.top = e.clientY + 'px';

            const width = parseFloat(pageObj.dataset.width);
            const height = parseFloat(pageObj.dataset.height);
            const imgObj = pageObj.querySelector('img');
            if (imgObj) {
                const imgRect = imgObj.getBoundingClientRect();
                // Toán học: (Tọa độ client - viền left ảnh) / chiều rộng ảnh hiển thị * Chiều rộng trang gốc PDF
                const x = ((e.clientX - imgRect.left) / imgRect.width) * width;
                const y = ((e.clientY - imgRect.top) / imgRect.height) * height;
                cursorTooltip.textContent = `X: ${x.toFixed(1)}, Y: ${y.toFixed(1)}`;
            }
        } else {
            cursorTooltip.style.display = 'none';
        }
    });

    document.addEventListener('mouseleave', () => {
        cursorTooltip.style.display = 'none';
    });
});
