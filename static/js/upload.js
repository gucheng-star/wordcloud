import { state, dom } from './state.js';
import { showMessage } from './utils.js';
import { loadStorageInfo } from './manage.js';

export function initUpload() {
    var fileSelectZone = document.getElementById('file-select-zone');
    var fileInput = document.getElementById('file-input');
    var filePreview = document.getElementById('file-preview');
    var previewName = document.getElementById('preview-name');
    var previewRemove = document.getElementById('preview-remove');
    var uploadForm = document.getElementById('upload-form');
    var uploadBtn = document.getElementById('upload-btn');

    fileSelectZone.addEventListener('click', function() { fileInput.click(); });

    fileInput.addEventListener('change', function() {
        if (fileInput.files.length > 0) {
            previewName.textContent = fileInput.files[0].name;
            filePreview.style.display = 'flex';
            fileSelectZone.style.display = 'none';
            uploadBtn.disabled = false;
        } else { resetFileSelect(); }
    });

    previewRemove.addEventListener('click', function() { resetFileSelect(); });

    function resetFileSelect() {
        fileInput.value = '';
        previewName.textContent = '';
        filePreview.style.display = 'none';
        fileSelectZone.style.display = 'flex';
        uploadBtn.disabled = true;
    }

    uploadForm.addEventListener('submit', function(event) {
        event.preventDefault();
        if (fileInput.files.length === 0) { showMessage('请先选择文件', 'error'); return; }
        uploadBtn.disabled = true;
        uploadBtn.textContent = '上传中...';

        var formData = new FormData();
        formData.append('file', fileInput.files[0]);
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/upload_txt', true);
        xhr.onload = function() {
            uploadBtn.textContent = '上传文件';
            if (xhr.status === 200) {
                var response = JSON.parse(xhr.responseText);
                if (response.status === 'success') {
                    showMessage(response.message, 'success');
                    state.currentFilename = response.filename;
                    state.currentOriginalName = response.original_name || response.filename;
                    dom.uploadedFilename.textContent = state.currentOriginalName;
                    dom.processArea.style.display = 'block';
                    dom.resultArea.style.display = 'none';
                    dom.cloudArea.style.display = 'none';
                    resetFileSelect();
                    loadStorageInfo();
                } else { showMessage(response.message, 'error'); uploadBtn.disabled = false; }
            } else { showMessage('服务器错误', 'error'); uploadBtn.disabled = false; }
        };
        xhr.onerror = function() { uploadBtn.textContent = '上传文件'; uploadBtn.disabled = false; showMessage('网络错误', 'error'); };
        xhr.send(formData);
    });
}
