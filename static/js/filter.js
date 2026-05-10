import { state, dom } from './state.js';
import { postJSON, showMessage } from './utils.js';

export function initFilter() {
    var selectAllBtn = document.getElementById('select-all-btn');
    var deselectAllBtn = document.getElementById('deselect-all-btn');
    var filterBtn = document.getElementById('filter-btn');

    selectAllBtn.addEventListener('click', function() {
        state.currentRemovedWords = Object.keys(state.currentOriginalWordFreq);
        renderWordFreq(state.currentOriginalWordFreq, state.currentRemovedWords);
    });

    deselectAllBtn.addEventListener('click', function() {
        state.currentRemovedWords = [];
        renderWordFreq(state.currentOriginalWordFreq, state.currentRemovedWords);
    });

    filterBtn.addEventListener('click', function() {
        filterBtn.disabled = true;
        filterBtn.textContent = '过滤中...';
        postJSON('/filter_words', { session_id: state.currentSessionId, remove_words: state.currentRemovedWords }, function(response) {
            filterBtn.disabled = false;
            filterBtn.textContent = '确认过滤';
            if (response.status === 'success') {
                if (state.currentRemovedWords.length === 0) {
                    showMessage('已取消所有过滤，所有词将参与词云生成', 'success');
                } else {
                    showMessage('过滤完成！已标记 ' + state.currentRemovedWords.length + ' 个词', 'success');
                }
                state.currentWordFreq = response.word_freq;
                state.currentOriginalWordFreq = response.original_word_freq || state.currentOriginalWordFreq;
                state.currentRemovedWords = response.removed_words || state.currentRemovedWords;
                renderWordFreq(state.currentOriginalWordFreq, state.currentRemovedWords);
            } else { showMessage(response.message, 'error'); }
        });
    });
}

export function renderWordFreq(originalWordFreq, removedWords) {
    dom.wordFreqList.innerHTML = '';
    var items = Object.entries(originalWordFreq).sort(function(a, b) { return b[1] - a[1]; });
    if (items.length === 0) {
        dom.wordFreqList.innerHTML = '<p class="empty-hint">所有词已被过滤</p>';
        dom.resultArea.style.display = 'block';
        return;
    }
    var removedSet = new Set(removedWords || []);
    for (var i = 0; i < items.length; i++) {
        var word = items[i][0];
        var freq = items[i][1];
        var isRemoved = removedSet.has(word);

        var tag = document.createElement('button');
        tag.type = 'button';
        tag.className = 'word-tag' + (isRemoved ? ' removed' : '');
        tag.setAttribute('data-word', word);
        tag.innerHTML = word + ' <span class="tag-count">' + freq + '</span>';

        tag.addEventListener('click', (function(w) {
            return function() { toggleWord(w); };
        })(word));

        dom.wordFreqList.appendChild(tag);
    }
    dom.resultArea.style.display = 'block';
}

function toggleWord(word) {
    var idx = state.currentRemovedWords.indexOf(word);
    if (idx === -1) {
        state.currentRemovedWords.push(word);
    } else {
        state.currentRemovedWords.splice(idx, 1);
    }
    renderWordFreq(state.currentOriginalWordFreq, state.currentRemovedWords);
}
