import { dom } from './state.js';
import { postJSON, showMessage, showConfirm } from './utils.js';

export function initManage() {
    var cleanUploadsBtn = document.getElementById('clean-uploads-btn');
    var cleanOutputsBtn = document.getElementById('clean-outputs-btn');

    cleanUploadsBtn.addEventListener('click', function() {
        showConfirm('确定清理所有上传的文本文件吗？此操作不可恢复。', function() {
            postJSON('/clean_uploads', {}, function(response) {
                if (response.status === 'success') {
                    showMessage('已清理 ' + response.deleted + ' 个文件，释放 ' + response.freed_kb + ' KB', 'success');
                    loadStorageInfo();
                }
            });
        });
    });

    cleanOutputsBtn.addEventListener('click', function() {
        showConfirm('确定清理所有词云图片吗？此操作不可恢复。', function() {
            postJSON('/clean_outputs', {}, function(response) {
                if (response.status === 'success') {
                    showMessage('已清理 ' + response.deleted + ' 个文件，释放 ' + response.freed_kb + ' KB', 'success');
                    loadStorageInfo();
                    dom.cloudResult.style.display = 'none';
                }
            });
        });
    });

    loadStorageInfo();
}

export function loadStorageInfo() {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/storage_info', true);
    xhr.onload = function() {
        if (xhr.status === 200) {
            var r = JSON.parse(xhr.responseText);
            if (r.status === 'success') {
                dom.storageInfo.innerHTML = '上传文件: <strong>' + r.uploads.files + '</strong> 个 (' + r.uploads.size_kb + ' KB) &nbsp;&nbsp; 词云图片: <strong>' + r.outputs.files + '</strong> 个 (' + r.outputs.size_kb + ' KB)';
            }
        }
    };
    xhr.send();
}
