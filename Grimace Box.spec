# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\Me\\anaconda3\\envs\\GrimaceRecorder\\Lib\\site-packages\\ultralytics\\cfg\\default.yaml', './ultralytics/cfg'), ('models/frame_quality.pt', './models'), ('models/face_cropper.pt', './models'), ('models/grimace_scorer.pt', './models'), ('camera_config/top.pfs', './camera_config'), ('camera_config/front.pfs', './camera_config')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Grimace Box',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['res\\grimace_box_icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Grimace Box',
)
