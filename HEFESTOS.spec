# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['hefestos.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('install_manifest.json', '.'),
        ('hefestos_key_validator.py', '.'),
        ('Resources/HEFESTOS.png', 'Resources'),
        ('Resources/HEFESTOS.ico', 'Resources'),
    ],
    hiddenimports=['hefestos_key_validator'],
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
    a.binaries,
    a.datas,
    [],
    name='HEFESTOS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='Resources/HEFESTOS.ico',
)
