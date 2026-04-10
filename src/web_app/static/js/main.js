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
        pdfHtml += `<div class="pdf-page">
            <img src="/api/page_image/${encodeURIComponent(currentFilename)}/${page.page_id}">`;

        // RENDER BÊN PHẢI (JSON ROOT)
        jsonHtml += `  {\n    <span class="j-key">"page_id"</span>: <span class="j-num">${page.page_id}</span>,\n    <span class="j-key">"width"</span>: <span class="j-num">${page.width}</span>,\n    <span class="j-key">"height"</span>: <span class="j-num">${page.height}</span>,\n    <span class="j-key">"text_blocks"</span>: [\n`;

        // LOOP BLOCK TEXT
        page.text_blocks.forEach((txt, idx) => {
            let bId = `page${page.page_id}-text${idx}`;
            
            let left = (txt.bbox[0] / page.width) * 100;
            let top = (txt.bbox[1] / page.height) * 100;
            let width = ((txt.bbox[2] - txt.bbox[0]) / page.width) * 100;
            let height = ((txt.bbox[3] - txt.bbox[1]) / page.height) * 100;
            
            pdfHtml += `<div class="bbox-overlay text-box" id="box-${bId}" style="left:${left}%; top:${top}%; width:${width}%; height:${height}%;" onclick="highlightUI('${bId}')"></div>`;
            
            let contentSafe = txt.content.replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\n/g, '\\n');
            jsonHtml += `<div class="json-block-node" id="json-${bId}">      {\n        <span class="j-key">"content"</span>: <span class="j-str">"${contentSafe}"</span>,\n        <span class="j-key">"bbox"</span>: [<span class="j-num">${txt.bbox.map(n => Math.round(n * 100) / 100).join(', ')}</span>]\n      }</div>${idx < page.text_blocks.length - 1 ? ',' : ''}\n`;
        });

        jsonHtml += `    ],\n    <span class="j-key">"image_blocks"</span>: [\n`;

        // LOOP BLOCK IMAGE 
        page.image_blocks.forEach((img, idx) => {
            let bId = `page${page.page_id}-img${idx}`;
            
            let left = (img.bbox[0] / page.width) * 100;
            let top = (img.bbox[1] / page.height) * 100;
            let width = ((img.bbox[2] - img.bbox[0]) / page.width) * 100;
            let height = ((img.bbox[3] - img.bbox[1]) / page.height) * 100;
            
            pdfHtml += `<div class="bbox-overlay img-box" id="box-${bId}" style="left:${left}%; top:${top}%; width:${width}%; height:${height}%;" onclick="highlightUI('${bId}')"></div>`;
            
            jsonHtml += `<div class="json-block-node" id="json-${bId}">      {\n        <span class="j-key">"bbox"</span>: [<span class="j-num">${img.bbox.map(n => Math.round(n * 100) / 100).join(', ')}</span>]\n      }</div>${idx < page.image_blocks.length - 1 ? ',' : ''}\n`;
        });

        pdfHtml += `</div>`;
        jsonHtml += `    ]\n  }${page.page_id < data.length ? ',' : ''}\n`;
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
    
    if (newBox) newBox.classList.add('active-highlight');

    if (newJson) {
        newJson.classList.add('active-highlight');
        newJson.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    currentHighlight = targetId;
}
