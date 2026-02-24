# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for Document Creator"""

import os
import sys

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('resources/icon.ico', 'resources'),
        ('resources/icon.icns', 'resources'),
        ('src/resources/help', 'help'),
        ('src/resources/icons', 'icons'),
        ('templates', 'templates'),
    ],
    hiddenimports=[
        'PyQt6',
        'PyQt6.QtWebEngineWidgets',
        # Excel 처리
        'openpyxl',
        'openpyxl.styles',
        'openpyxl.drawing.image',
        'openpyxl.utils',
        'openpyxl.workbook.defined_name',
        # PDF
        'fitz',
        # 이미지
        'PIL',
        # 템플릿
        'jinja2',
        # 라이센스 모듈
        'src.license',
        'src.license.hardware_id',
        'src.license.license_validator',
        'src.license.license_manager',
        'src.license.license_dialog',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# onedir 모드: EXE는 스크립트만 포함
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DocumentCreator',
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
    icon='resources/icon.ico',
)

# onedir 모드: COLLECT로 모든 파일 수집
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DocumentCreator',
)

# macOS 앱 번들
app = BUNDLE(
    coll,
    name='DocumentCreator.app',
    icon='resources/icon.icns',
    bundle_identifier='com.safetydoc.documentcreator',
    info_plist={
        'NSHighResolutionCapable': 'True',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleName': 'Document Creator',
        'CFBundleDisplayName': 'Document Creator',
    },
)
