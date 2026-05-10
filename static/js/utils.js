import { dom } from './state.js';

export function postJSON(url, data, callback) {
    var xhr = new XMLHttpRequest();
    xhr.open('POST', url, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onload = function() {
        if (xhr.status === 200) callback(JSON.parse(xhr.responseText));
        else callback({ status: 'error', message: '服务器错误' });
    };
    xhr.onerror = function() { callback({ status: 'error', message: '网络错误' }); };
    xhr.send(JSON.stringify(data));
}

export function showMessage(text, type) {
    dom.messageBox.textContent = text;
    dom.messageBox.className = 'message ' + type;
    dom.messageBox.style.display = 'block';
    setTimeout(function() { dom.messageBox.style.display = 'none'; }, 3000);
}

var confirmModal = document.getElementById('confirm-modal');
var confirmMessage = document.getElementById('confirm-message');
var confirmOk = document.getElementById('confirm-ok');
var confirmCancel = document.getElementById('confirm-cancel');
var confirmCallback = null;

export function showConfirm(message, onConfirm) {
    confirmMessage.textContent = message;
    confirmModal.style.display = 'flex';
    confirmCallback = onConfirm;
}

confirmOk.addEventListener('click', function() {
    confirmModal.style.display = 'none';
    if (confirmCallback) confirmCallback();
    confirmCallback = null;
});

confirmCancel.addEventListener('click', function() {
    confirmModal.style.display = 'none';
    confirmCallback = null;
});

confirmModal.addEventListener('click', function(e) {
    if (e.target === confirmModal) {
        confirmModal.style.display = 'none';
        confirmCallback = null;
    }
});
