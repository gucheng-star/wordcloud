import { state, dom } from './state.js';
import { postJSON, showMessage } from './utils.js';
import { renderWordFreq } from './filter.js';

export function initTextInput() {
    var textInput = document.getElementById('text-input');
    var charCount = document.getElementById('char-count');
    var textSubmitBtn = document.getElementById('text-submit-btn');

    textInput.addEventListener('input', function() {
        charCount.textContent = textInput.value.length + ' 字';
    });

    textSubmitBtn.addEventListener('click', function() {
        var text = textInput.value.trim();
        if (!text) { showMessage('请输入文本内容', 'error'); return; }

        textSubmitBtn.disabled = true;
        textSubmitBtn.textContent = '分析中...';

        postJSON('/process_text_input', { text: text }, function(response) {
            textSubmitBtn.disabled = false;
            textSubmitBtn.textContent = '开始分析';
            if (response.status === 'success') {
                showMessage('分词分析完成！', 'success');
                state.currentSessionId = response.session_id;
                state.currentWordFreq = response.word_freq;
                state.currentOriginalWordFreq = response.original_word_freq || response.word_freq;
                state.currentRemovedWords = response.removed_words || [];
                state.currentOriginalName = '直接输入文本';
                renderWordFreq(state.currentOriginalWordFreq, state.currentRemovedWords);
                dom.cloudArea.style.display = 'block';
                dom.cloudResult.style.display = 'none';
                dom.processArea.style.display = 'none';
            } else {
                showMessage(response.message, 'error');
            }
        });
    });
}
