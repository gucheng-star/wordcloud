import { dom } from './state.js';
import { postJSON, showMessage, showConfirm } from './utils.js';

export function initManage() {
    var cleanUploadsBtn = document.getElementById('clean-uploads-btn');
    var cleanOutputsBtn = document.getElementById('clean-outputs-btn');
    var cleanMasksBtn = document.getElementById('clean-masks-btn');

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

    cleanMasksBtn.addEventListener('click', function() {
        showConfirm('确定清理所有 Mask 图片吗？此操作不可恢复。', function() {
            postJSON('/clean_masks', {}, function(response) {
                if (response.status === 'success') {
                    showMessage('已清理 ' + response.deleted + ' 个文件，释放 ' + response.freed_kb + ' KB', 'success');
                    loadStorageInfo();
                }
            });
        });
    });

    loadStorageInfo();
}

export function loadStorageInfo() {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/storage_info', true);
    xhr.timeout = 5000;
    xhr.onload = function() {
        if (xhr.status === 200) {
            try {
                var r = JSON.parse(xhr.responseText);
                if (r.status === 'success') {
                    var masks = r.masks || {'files': 0, 'size_kb': 0};
                    dom.storageInfo.innerHTML =
                        '上传文件: <strong>' + r.uploads.files + '</strong> 个 (' + r.uploads.size_kb + ' KB)' +
                        ' &nbsp;&nbsp; 词云图片: <strong>' + r.outputs.files + '</strong> 个 (' + r.outputs.size_kb + ' KB)' +
                        ' &nbsp;&nbsp; Mask图片: <strong>' + masks.files + '</strong> 个 (' + masks.size_kb + ' KB)';
                } else {
                    dom.storageInfo.innerHTML = '加载失败';
                }
            } catch (e) {
                dom.storageInfo.innerHTML = '数据解析失败';
            }
        } else {
            dom.storageInfo.innerHTML = '加载失败 (HTTP ' + xhr.status + ')';
        }
    };
    xhr.onerror = function() {
        dom.storageInfo.innerHTML = '网络错误，无法加载存储信息';
    };
    xhr.ontimeout = function() {
        dom.storageInfo.innerHTML = '请求超时，请检查服务器';
    };
    xhr.send();
}
