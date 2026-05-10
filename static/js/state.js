export const state = {
    currentFilename: '',
    currentOriginalName: '',
    currentSessionId: '',
    currentWordFreq: {},
    currentOriginalWordFreq: {},
    currentRemovedWords: [],
    maskFilename: '',
    grayscaleFilename: '',
    grayscaleReady: false
};

export const dom = {
    messageBox: document.getElementById('message'),
    processArea: document.getElementById('process-area'),
    uploadedFilename: document.getElementById('uploaded-filename'),
    processBtn: document.getElementById('process-btn'),
    resultArea: document.getElementById('result-area'),
    wordFreqList: document.getElementById('word-freq-list'),
    cloudArea: document.getElementById('cloud-area'),
    cloudResult: document.getElementById('cloud-result'),
    cloudImage: document.getElementById('cloud-image'),
    downloadBtn: document.getElementById('download-btn'),
    historyList: document.getElementById('history-list'),
    storageInfo: document.getElementById('storage-info'),
    generateBtn: document.getElementById('generate-btn'),
    maskGenerateBtn: document.getElementById('mask-generate-btn'),
    filterBtn: document.getElementById('filter-btn')
};
