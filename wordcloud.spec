# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

BASE_DIR = os.path.abspath('.')

a = Analysis(
    ['app.py'],
    pathex=[BASE_DIR],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('stopwords.txt', '.'),
    ],
    hiddenimports=[
        'utils.text_processor',
        'utils.filter_processor',
        'utils.cloud_generator',
        'utils.color_manager',
        'utils.mask_processor',
        'utils.history_manager',
        'jieba',
        'wordcloud',
        'PIL',
        'numpy',
        'matplotlib',
        'flask',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'scipy',
        'pandas',
        'IPython',
        'notebook',
        'sphinx',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='中文词云工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='中文词云工具',
)
