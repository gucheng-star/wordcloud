import { initTabs } from './tabs.js';
import { initUpload } from './upload.js';
import { initTextInput } from './text-input.js';
import { initProcess } from './process.js';
import { initFilter } from './filter.js';
import { initCloud } from './cloud.js';
import { initMask } from './mask.js';
import { initHistory } from './history.js';
import { initManage } from './manage.js';

var initFunctions = [
    ['标签切换', initTabs],
    ['文件上传', initUpload],
    ['文本输入', initTextInput],
    ['分词处理', initProcess],
    ['词频过滤', initFilter],
    ['词云生成', initCloud],
    ['灰度处理', initMask],
    ['历史记录', initHistory],
    ['数据管理', initManage]
];

initFunctions.forEach(function(item) {
    try {
        item[1]();
    } catch (e) {
        console.error('[初始化失败] ' + item[0] + ':', e);
    }
});
