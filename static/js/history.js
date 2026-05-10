import { state, dom } from './state.js';
import { postJSON, showMessage, showConfirm } from './utils.js';
import { renderWordFreq } from './filter.js';
import { updateGenerateBtnState } from './cloud.js';

export function initHistory() {
    loadHistoryList();

    var clearBtn = document.getElementById('clear-history-btn');
    clearBtn.addEventListener('click', function() {
        showConfirm('确定清空所有历史记录吗？此操作不可恢复！', function() {
            postJSON('/clear_all_history', {}, function(response) {
                if (response.status === 'success') {
                    showMessage('已清空 ' + response.deleted + ' 条历史记录', 'success');
                    loadHistoryList();
                } else { showMessage(response.message, 'error'); }
            });
        });
    });
}

export function loadHistoryList() {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/history_list', true);
    xhr.onload = function() {
        if (xhr.status === 200) {
            var response = JSON.parse(xhr.responseText);
            if (response.status === 'success') renderHistoryList(response.history);
        }
    };
    xhr.send();
}

function renderHistoryList(history) {
    dom.historyList.innerHTML = '';
    if (history.length === 0) { dom.historyList.innerHTML = '<p class="history-empty">暂无历史记录</p>'; return; }
    for (var i = 0; i < history.length; i++) {
        var record = history[i];
        var item = document.createElement('div');
        item.className = 'history-item';
        var info = document.createElement('div');
        info.className = 'history-info';
        var timeEl = document.createElement('div');
        timeEl.className = 'history-time';
        timeEl.textContent = record.time;
        var nameEl = document.createElement('div');
        nameEl.className = 'history-name';
        nameEl.textContent = record.filename || '未知文件';
        var topWords = Object.entries(record.word_freq || {}).sort(function(a, b) { return b[1] - a[1]; }).slice(0, 3).map(function(w) { return w[0] + '(' + w[1] + ')'; }).join('、');
        var freqEl = document.createElement('div');
        freqEl.className = 'history-freq';
        freqEl.textContent = topWords || '无词频数据';
        info.appendChild(timeEl);
        info.appendChild(nameEl);
        info.appendChild(freqEl);
        var actions = document.createElement('div');
        actions.className = 'history-actions';
        var regenBtn = document.createElement('button');
        regenBtn.className = 'btn-regen';
        regenBtn.textContent = '重新生成';
        regenBtn.setAttribute('data-id', record.id);
        var delBtn = document.createElement('button');
        delBtn.className = 'btn-del';
        delBtn.textContent = '删除';
        delBtn.setAttribute('data-id', record.id);
        actions.appendChild(regenBtn);
        actions.appendChild(delBtn);
        item.appendChild(info);
        item.appendChild(actions);
        dom.historyList.appendChild(item);
    }
    dom.historyList.querySelectorAll('.btn-regen').forEach(function(btn) {
        btn.addEventListener('click', function() { regenerateFromHistory(this.getAttribute('data-id')); });
    });
    dom.historyList.querySelectorAll('.btn-del').forEach(function(btn) {
        btn.addEventListener('click', function() { deleteHistoryRecord(this.getAttribute('data-id')); });
    });
}

function regenerateFromHistory(recordId) {
    postJSON('/load_history', { id: recordId }, function(response) {
        if (response.status === 'success') {
            var params = response.params || {};
            var wordFreq = response.word_freq || {};
            state.currentWordFreq = wordFreq;
            state.currentOriginalWordFreq = dict(wordFreq);
            state.currentRemovedWords = [];
            renderWordFreq(state.currentOriginalWordFreq, state.currentRemovedWords);
            dom.cloudResult.style.display = 'none';

            var maxFontInput = document.getElementById('max-font');
            var minFontInput = document.getElementById('min-font');
            var cloudWidthInput = document.getElementById('cloud-width');
            var cloudHeightInput = document.getElementById('cloud-height');
            var colorThemeSelect = document.getElementById('color-theme');
            var colorHexInput = document.getElementById('color-hex');
            var colorPicker = document.getElementById('color-picker');
            var colorHexRow = document.getElementById('color-hex-row');

            maxFontInput.value = params.max_font_size || 80;
            minFontInput.value = params.min_font_size || 20;
            cloudWidthInput.value = params.width || 800;
            cloudHeightInput.value = params.height || 600;

            if (params.color_hex) {
                colorThemeSelect.value = 'custom';
                colorHexInput.value = params.color_hex;
                colorPicker.value = params.color_hex;
                colorHexRow.style.display = 'flex';
            } else {
                colorThemeSelect.value = params.color_theme || 'blue';
                colorHexInput.value = '';
                colorHexRow.style.display = 'none';
            }

            postJSON('/cache_word_freq', { word_freq: wordFreq }, function(resp) {
                if (resp.status === 'success') {
                    state.currentSessionId = resp.session_id;
                    updateGenerateBtnState();
                    showMessage('历史记录已加载，点击"生成词云"', 'success');
                }
            });
        } else { showMessage(response.message, 'error'); }
    });
}

function deleteHistoryRecord(recordId) {
    showConfirm('确定删除这条历史记录吗？', function() {
        postJSON('/delete_history', { id: recordId }, function(response) {
            if (response.status === 'success') { showMessage('已删除', 'success'); loadHistoryList(); }
            else { showMessage(response.message, 'error'); }
        });
    });
}

function dict(obj) { var o = {}; for (var k in obj) { if (obj.hasOwnProperty(k)) o[k] = obj[k]; } return o; }
