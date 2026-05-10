export function initTabs() {
    var tabFile = document.getElementById('tab-file');
    var tabText = document.getElementById('tab-text');
    var panelFile = document.getElementById('panel-file');
    var panelText = document.getElementById('panel-text');

    tabFile.addEventListener('click', function() {
        tabFile.classList.add('active');
        tabText.classList.remove('active');
        panelFile.style.display = '';
        panelText.style.display = 'none';
    });

    tabText.addEventListener('click', function() {
        tabText.classList.add('active');
        tabFile.classList.remove('active');
        panelText.style.display = '';
        panelFile.style.display = 'none';
    });
}
