block_cipher = None
from PyInstaller.utils.hooks import collect_submodules
hidden = (
    collect_submodules('fastapi')
    + collect_submodules('starlette')
    + collect_submodules('uvicorn')
    + collect_submodules('anyio')
)
a = Analysis(
    ['src/fastform/app_entry.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=hidden,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name='FastForm',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False
)
app = BUNDLE(
    exe,
    name='FastForm.app',
    icon=None,
    bundle_identifier='com.fastform.app',
)
