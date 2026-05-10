import { state, dom } from './state.js';
import { postJSON, showMessage } from './utils.js';
import { loadStorageInfo } from './manage.js';

export function initMask() {
    var maskUploadZone = document.getElementById('mask-upload-zone');
    var maskFileInput = document.getElementById('mask-file-input');
    var maskPreview = document.getElementById('mask-preview');
    var maskPreviewImg = document.getElementById('mask-preview-img');
    var maskPreviewName = document.getElementById('mask-preview-name');
    var maskPreviewRemove = document.getElementById('mask-preview-remove');
    var thresholdSlider = document.getElementById('threshold-slider');
    var thresholdValue = document.getElementById('threshold-value');
    var overlaySlider = document.getElementById('overlay-slider');
    var overlayValue = document.getElementById('overlay-value');
    var grayscaleBtn = document.getElementById('grayscale-btn');
    var invertBtn = document.getElementById('invert-btn');
    var grayscalePreview = document.getElementById('grayscale-preview');
    var grayscalePreviewImg = document.getElementById('grayscale-preview-img');
    var grayscaleInfo = document.getElementById('grayscale-info');

    maskUploadZone.addEventListener('click', function() { maskFileInput.click(); });

    maskFileInput.addEventListener('change', function() {
        if (maskFileInput.files.length > 0) {
            uploadMaskImage(maskFileInput.files[0]);
            maskFileInput.value = '';
        }
    });

    maskPreviewRemove.addEventListener('click', function() {
        state.maskFilename = '';
        state.grayscaleFilename = '';
        state.grayscaleReady = false;
        maskPreview.style.display = 'none';
        maskPreviewImg.src = '';
        maskUploadZone.style.display = 'flex';
        grayscaleBtn.disabled = true;
        invertBtn.disabled = true;
        grayscalePreview.style.display = 'none';
        grayscalePreviewImg.src = '';
        grayscaleInfo.textContent = '';
        dom.maskGenerateBtn.disabled = true;
    });

    thresholdSlider.addEventListener('input', function() {
        thresholdValue.textContent = thresholdSlider.value;
    });

    overlaySlider.addEventListener('input', function() {
        overlayValue.textContent = overlaySlider.value + '%';
    });

    grayscaleBtn.addEventListener('click', function() {
        if (!state.maskFilename) { showMessage('请先上传图片', 'error'); return; }

        grayscaleBtn.disabled = true;
        grayscaleBtn.textContent = '生成中...';

        var params = {
            mask_filename: state.maskFilename,
            threshold: parseInt(thresholdSlider.value),
            invert: false
        };

        postJSON('/generate_grayscale', params, function(response) {
            grayscaleBtn.disabled = false;
            grayscaleBtn.textContent = '生成灰度图片';
            if (response.status === 'success') {
                showMessage('灰度图片生成成功！', 'success');
                state.grayscaleFilename = response.grayscale_filename;
                state.grayscaleReady = true;
                grayscalePreviewImg.src = response.grayscale_url + '?t=' + Date.now();
                grayscaleInfo.textContent = '尺寸: ' + response.width + '×' + response.height;
                grayscalePreview.style.display = 'block';
                invertBtn.disabled = false;
                updateMaskGenerateBtnState();
                loadStorageInfo();
            } else { showMessage(response.message, 'error'); }
        });
    });

    invertBtn.addEventListener('click', function() {
        var sourceFilename = state.grayscaleFilename || state.maskFilename;
        if (!sourceFilename) { showMessage('请先生成灰度图片', 'error'); return; }

        invertBtn.disabled = true;
        invertBtn.textContent = '反转中...';

        var params = {
            grayscale_filename: sourceFilename,
            threshold: parseInt(thresholdSlider.value)
        };

        postJSON('/invert_grayscale', params, function(response) {
            invertBtn.disabled = false;
            invertBtn.textContent = '灰度反转';
            if (response.status === 'success') {
                showMessage('灰度反转成功！', 'success');
                state.grayscaleFilename = response.grayscale_filename;
                state.grayscaleReady = true;
                grayscalePreviewImg.src = response.grayscale_url + '?t=' + Date.now();
                grayscaleInfo.textContent = '尺寸: ' + response.width + '×' + response.height + '（已反转）';
                grayscalePreview.style.display = 'block';
                updateMaskGenerateBtnState();
                loadStorageInfo();
            } else { showMessage(response.message, 'error'); }
        });
    });

    function updateMaskGenerateBtnState() {
        if (state.grayscaleReady && state.currentSessionId) {
            dom.maskGenerateBtn.disabled = false;
        } else {
            dom.maskGenerateBtn.disabled = true;
        }
    }

    function uploadMaskImage(file) {
        var formData = new FormData();
        formData.append('file', file);
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/upload_mask_image', true);
        xhr.onload = function() {
            if (xhr.status === 200) {
                var response = JSON.parse(xhr.responseText);
                if (response.status === 'success') {
                    state.maskFilename = response.mask_filename;
                    state.grayscaleFilename = '';
                    state.grayscaleReady = false;
                    maskPreviewName.textContent = file.name;
                    maskPreviewImg.src = '/masks/' + response.mask_filename;
                    maskPreview.style.display = 'flex';
                    maskUploadZone.style.display = 'none';
                    grayscaleBtn.disabled = false;
                    invertBtn.disabled = true;
                    grayscalePreview.style.display = 'none';
                    grayscalePreviewImg.src = '';
                    grayscaleInfo.textContent = '';
                    dom.maskGenerateBtn.disabled = true;
                    if (response.preview) {
                        showMessage('图片上传成功，尺寸: ' + response.preview.width + '×' + response.preview.height, 'success');
                    } else {
                        showMessage('图片上传成功', 'success');
                    }
                    loadStorageInfo();
                } else { showMessage(response.message, 'error'); }
            } else { showMessage('服务器错误', 'error'); }
        };
        xhr.onerror = function() { showMessage('网络错误', 'error'); };
        xhr.send(formData);
    }
}

export function updateMaskGenerateBtnState() {
    var btn = document.getElementById('mask-generate-btn');
    if (state.grayscaleReady && state.currentSessionId) {
        btn.disabled = false;
    } else {
        btn.disabled = true;
    }
}
