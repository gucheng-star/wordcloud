import { state, dom } from './state.js';
import { postJSON, showMessage } from './utils.js';
import { renderWordFreq } from './filter.js';
import { updateGenerateBtnState } from './cloud.js';

export function initProcess() {
    dom.processBtn.addEventListener('click', function() {
        if (!state.currentFilename) { showMessage('请先上传文件', 'error'); return; }
        dom.processBtn.disabled = true;
        dom.processBtn.textContent = '分析中...';
        postJSON('/process_text', { filename: state.currentFilename }, function(response) {
            dom.processBtn.disabled = false;
            dom.processBtn.textContent = '开始分词分析';
            if (response.status === 'success') {
                showMessage('分词分析完成！', 'success');
                state.currentSessionId = response.session_id;
                state.currentWordFreq = response.word_freq;
                state.currentOriginalWordFreq = response.original_word_freq || response.word_freq;
                state.currentRemovedWords = response.removed_words || [];
                renderWordFreq(state.currentOriginalWordFreq, state.currentRemovedWords);
                dom.cloudResult.style.display = 'none';
                updateGenerateBtnState();
            } else { showMessage(response.message, 'error'); }
        });
    });
}
