import sys
import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files, collect_dynamic_libs, copy_metadata
datas = []
datas += copy_metadata('streamlit')

# Collect all submodules from your src package
hiddenimports = collect_submodules('src')

# Collect wxPython dynamic libraries including SDL2
wx_binaries = []
try:
    # Adding wxPython dynamic libraries
    wx_binaries.extend(collect_dynamic_libs('wx'))
    
    # Adding SDL2 libraries specifically for macOS
    if sys.platform == 'darwin':
        import subprocess
        brew_prefix = subprocess.check_output(['brew', '--prefix']).decode().strip()
        # Adding the specific SDL2 libraries we found
        sdl_paths = [
            os.path.join(brew_prefix, 'lib/libSDL2-2.0.0.dylib'),
            os.path.join(brew_prefix, 'lib/libSDL2.dylib'),
        ]
        for sdl_path in sdl_paths:
            if os.path.exists(sdl_path):
                wx_binaries.append((sdl_path, '.'))
                print(f"Adding SDL2 library: {sdl_path}")
except Exception as e:
    print(f"Warning: Could not collect binaries: {e}")

# Collect data files (e.g., images) from the Images directory
datas = [
    (os.path.join('_internal/images', '*'), '_internal/images'),
]

block_cipher = None

a = Analysis(
    ['BenBox.py'],
    pathex=['.'],
    binaries=wx_binaries,
    datas=datas,
    hiddenimports=[
        'mcp',
        'mcp.server',
        'mcp.server.fastmcp',
        'mcp.server.models',
        'mcp.types'
    ],
    hookspath=[],
    excludes=[
        'mysql',
        'mysql.vendor',
        'streamlit',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

# Create a GUI executable without a console
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='BenBox',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to False for GUI apps
    icon=os.path.join('_internal/images', 'icon.ico')
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='BenBox'
)

app = BUNDLE(
    coll,
    name='BenBox.app',
    icon=os.path.join('_internal/images', 'icon.icns'),
    info_plist={
        'CFBundleName': 'BenBox',
        'CFBundleShortVersionString': '0.1.0',
        'CFBundleVersion': '0.1.0',
        'CFBundleIdentifier': 'org.seriousbenentertainment.BenBox'
    }
)