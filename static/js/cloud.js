import { state, dom } from './state.js';
import { postJSON, showMessage } from './utils.js';
import { loadHistoryList } from './history.js';
import { loadStorageInfo } from './manage.js';

export function initCloud() {
    var maxFontInput = document.getElementById('max-font');
    var minFontInput = document.getElementById('min-font');
    var colorThemeSelect = document.getElementById('color-theme');
    var cloudWidthInput = document.getElementById('cloud-width');
    var cloudHeightInput = document.getElementById('cloud-height');
    var colorHexRow = document.getElementById('color-hex-row');
    var colorHexInput = document.getElementById('color-hex');
    var colorPicker = document.getElementById('color-picker');
    var generateBtn = document.getElementById('generate-btn');

    colorThemeSelect.addEventListener('change', function() {
        if (colorThemeSelect.value === 'custom') {
            colorHexRow.style.display = 'flex';
        } else {
            colorHexRow.style.display = 'none';
            colorHexInput.value = '';
        }
    });

    colorPicker.addEventListener('input', function() {
        colorHexInput.value = colorPicker.value;
    });

    colorHexInput.addEventListener('input', function() {
        var val = colorHexInput.value.trim();
        if (/^#[0-9a-fA-F]{6}$/.test(val)) {
            colorPicker.value = val;
        }
    });

    generateBtn.addEventListener('click', function() {
        if (!state.currentSessionId) { showMessage('请先进行分词分析', 'error'); return; }
        generateBtn.disabled = true;
        generateBtn.textContent = '生成中...';

        var colorHex = '';
        if (colorThemeSelect.value === 'custom') {
            colorHex = colorHexInput.value.trim();
            if (!colorHex) { showMessage('请输入自定义颜色（如 #3366ff）', 'error'); generateBtn.disabled = false; generateBtn.textContent = '生成词云'; return; }
            if (!/^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/.test(colorHex)) { showMessage('颜色格式不正确，请输入如 #ff0000 或 #f00', 'error'); generateBtn.disabled = false; generateBtn.textContent = '生成词云'; return; }
        }

        var params = {
            session_id: state.currentSessionId,
            max_font_size: parseInt(maxFontInput.value) || 80,
            min_font_size: parseInt(minFontInput.value) || 20,
            color_theme: colorThemeSelect.value === 'custom' ? 'blue' : colorThemeSelect.value,
            color_hex: colorHex,
            width: parseInt(cloudWidthInput.value) || 800,
            height: parseInt(cloudHeightInput.value) || 600
        };
        postJSON('/generate_wordcloud', params, function(response) {
            generateBtn.disabled = false;
            generateBtn.textContent = '生成词云';
            if (response.status === 'success') {
                showMessage('词云生成成功！', 'success');
                dom.cloudImage.src = response.image_url + '?t=' + Date.now();
                dom.downloadBtn.href = '/download_image/' + response.image_url.split('/').pop();
                dom.cloudResult.style.display = 'block';
                saveCurrentHistory(params);
                loadStorageInfo();
            } else { showMessage(response.message, 'error'); }
        });
    });
}

function saveCurrentHistory(params) {
    postJSON('/save_history', {
        word_freq: state.currentWordFreq,
        params: {
            max_font_size: params.max_font_size,
            min_font_size: params.min_font_size,
            color_theme: params.color_theme,
            color_hex: params.color_hex || '',
            width: params.width,
            height: params.height
        },
        filename: state.currentOriginalName || state.currentFilename
    }, function(response) { if (response.status === 'success') loadHistoryList(); });
}
