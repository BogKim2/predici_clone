# -*- mode: python ; coding: utf-8 -*-

block_cipher = None
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

ROOT = Path(SPECPATH).parent
if ROOT.name == 'packaging':
    ROOT = ROOT.parent

a = Analysis(
    [str(ROOT / 'predici_clone' / 'app' / 'main.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[],
    hiddenimports=[
        'scipy',
        'matplotlib.backends.backend_qtagg',
        'PySide6',
        'openpyxl',
        'networkx',
        *collect_submodules('predici_clone.montecarlo'),
        *collect_submodules('predici_clone.psd'),
        *collect_submodules('predici_clone.emulsion'),
        *collect_submodules('predici_clone.thermo'),
        *collect_submodules('test_manuals'),
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'accelerate',
        'aiohttp',
        'altair',
        'boto3',
        'botocore',
        'cv2',
        'datasets',
        'diffusers',
        'fastapi',
        'google',
        'grpc',
        'huggingface_hub',
        'langchain',
        'langchain_classic',
        'langchain_community',
        'librosa',
        'lightgbm',
        'litellm',
        'numba',
        'openai',
        'sklearn',
        'tensorflow',
        'torch',
        'transformers',
        'uvicorn',
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
    name='PrediciClone',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PrediciClone',
)
