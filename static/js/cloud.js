import { state, dom } from './state.js';
import { postJSON, showMessage } from './utils.js';
import { loadHistoryList } from './history.js';
import { loadStorageInfo } from './manage.js';
import { updateMaskGenerateBtnState } from './mask.js';

export function initCloud() {
    var maxFontInput = document.getElementById('max-font');
    var minFontInput = document.getElementById('min-font');
    var cloudWidthInput = document.getElementById('cloud-width');
    var cloudHeightInput = document.getElementById('cloud-height');
    var colorModeSelect = document.getElementById('color-mode');
    var gradientThemeSelect = document.getElementById('gradient-theme');
    var gradientThemeRow = document.getElementById('gradient-theme-row');
    var colorHexRow = document.getElementById('color-hex-row');
    var colorHexInput = document.getElementById('color-hex');
    var colorPicker = document.getElementById('color-picker');
    var generateBtn = document.getElementById('generate-btn');
    var maskGenerateBtn = document.getElementById('mask-generate-btn');
    var overlaySlider = document.getElementById('overlay-slider');
    var layoutStyleSelect = document.getElementById('layout-style');
    var fontFamilySelect = document.getElementById('font-family');

    var fontCssMap = {
        'yahei': "'Microsoft YaHei', sans-serif",
        'simhei': "'SimHei', sans-serif",
        'simsun': "'SimSun', serif",
        'simkai': "'KaiTi', serif",
        'simfang': "'FangSong', serif"
    };

    fontFamilySelect.addEventListener('change', function() {
        fontFamilySelect.style.fontFamily = fontCssMap[fontFamilySelect.value] || fontCssMap['yahei'];
    });

    function updateColorUI() {
        var mode = colorModeSelect.value;
        if (mode === 'preset_gradient') {
            gradientThemeRow.style.display = 'flex';
            colorHexRow.style.display = 'none';
        } else if (mode === 'auto_gradient') {
            gradientThemeRow.style.display = 'none';
            colorHexRow.style.display = 'flex';
        } else {
            gradientThemeRow.style.display = 'none';
            colorHexRow.style.display = 'flex';
        }
    }

    updateColorUI();

    colorModeSelect.addEventListener('change', updateColorUI);

    colorPicker.addEventListener('input', function() {
        colorHexInput.value = colorPicker.value;
    });

    colorHexInput.addEventListener('input', function() {
        var val = colorHexInput.value.trim();
        if (/^#[0-9a-fA-F]{6}$/.test(val)) {
            colorPicker.value = val;
        }
    });

    function getColorParams() {
        var mode = colorModeSelect.value;
        var params = {
            color_mode: mode,
            gradient_theme: gradientThemeSelect.value,
            base_color: ''
        };

        if (mode === 'solid' || mode === 'auto_gradient') {
            var hex = colorHexInput.value.trim();
            if (!hex) {
                hex = colorPicker.value;
            }
            if (!/^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/.test(hex)) {
                return { error: '颜色格式不正确，请输入如 #ff0000 或 #f00' };
            }
            params.base_color = hex;
        }

        return params;
    }

    generateBtn.addEventListener('click', function() {
        if (!state.currentSessionId) { showMessage('请先进行分词分析', 'error'); return; }

        var colorParams = getColorParams();
        if (colorParams.error) {
            showMessage(colorParams.error, 'error');
            return;
        }

        generateBtn.disabled = true;
        generateBtn.textContent = '生成中...';

        var params = {
            session_id: state.currentSessionId,
            max_font_size: parseInt(maxFontInput.value) || 80,
            min_font_size: parseInt(minFontInput.value) || 20,
            color_mode: colorParams.color_mode,
            gradient_theme: colorParams.gradient_theme,
            base_color: colorParams.base_color,
            width: parseInt(cloudWidthInput.value) || 800,
            height: parseInt(cloudHeightInput.value) || 600,
            layout_style: layoutStyleSelect.value,
            font_family: fontFamilySelect.value
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

    maskGenerateBtn.addEventListener('click', function() {
        if (!state.currentSessionId) { showMessage('请先进行分词分析', 'error'); return; }
        if (!state.grayscaleReady || !state.grayscaleFilename) { showMessage('请先生成灰度图片', 'error'); return; }

        var colorParams = getColorParams();
        if (colorParams.error) {
            showMessage(colorParams.error, 'error');
            return;
        }

        maskGenerateBtn.disabled = true;
        maskGenerateBtn.textContent = '生成中...';

        var overlayOpacity = parseInt(overlaySlider.value) / 100;

        var params = {
            session_id: state.currentSessionId,
            mask_filename: state.grayscaleFilename,
            original_mask_filename: state.maskFilename,
            threshold: parseInt(document.getElementById('threshold-slider').value),
            overlay_opacity: overlayOpacity,
            max_font_size: parseInt(maxFontInput.value) || 80,
            min_font_size: parseInt(minFontInput.value) || 20,
            color_mode: colorParams.color_mode,
            gradient_theme: colorParams.gradient_theme,
            base_color: colorParams.base_color,
            layout_style: layoutStyleSelect.value,
            font_family: fontFamilySelect.value
        };

        postJSON('/generate_mask_wordcloud', params, function(response) {
            maskGenerateBtn.disabled = false;
            maskGenerateBtn.textContent = '生成形状词云';
            if (response.status === 'success') {
                showMessage('形状词云生成成功！', 'success');
                dom.cloudImage.src = response.image_url + '?t=' + Date.now();
                dom.downloadBtn.href = '/download_image/' + response.image_url.split('/').pop();
                dom.cloudResult.style.display = 'block';
                loadStorageInfo();
            } else { showMessage(response.message, 'error'); }
        });
    });
}

export function updateGenerateBtnState() {
    if (state.currentSessionId) {
        dom.generateBtn.disabled = false;
        dom.filterBtn.disabled = false;
    } else {
        dom.generateBtn.disabled = true;
        dom.filterBtn.disabled = true;
    }
    updateMaskGenerateBtnState();
}

function saveCurrentHistory(params) {
    postJSON('/save_history', {
        word_freq: state.currentWordFreq,
        params: {
            max_font_size: params.max_font_size,
            min_font_size: params.min_font_size,
            color_mode: params.color_mode || 'preset_gradient',
            gradient_theme: params.gradient_theme || 'blue_gradient',
            base_color: params.base_color || '',
            width: params.width,
            height: params.height,
            layout_style: params.layout_style || 'classic',
            font_family: params.font_family || 'yahei'
        },
        filename: state.currentOriginalName || state.currentFilename
    }, function(response) { if (response.status === 'success') loadHistoryList(); });
}
