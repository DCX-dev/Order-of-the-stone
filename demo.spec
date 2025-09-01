# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_data_files

# Get the current directory
current_dir = os.getcwd()

# Define paths
game_assets_path = os.path.join(current_dir, 'Order of the stone', 'assets')
save_data_path = os.path.join(current_dir, 'Order of the stone', 'save_data')
main_script_path = os.path.join(current_dir, 'Order of the stone', 'assets', 'com', 'dreamcrusherx', 'Order of the stone', 'main_script', 'order_of_the_stone.py')

# Collect all data files from the game assets
datas = []

# Add all game assets
if os.path.exists(game_assets_path):
    for root, dirs, files in os.walk(game_assets_path):
        for file in files:
            src_path = os.path.join(root, file)
            # Calculate relative path from game_assets_path
            rel_path = os.path.relpath(src_path, game_assets_path)
            dest_path = os.path.join('Order of the stone', 'assets', rel_path)
            datas.append((src_path, dest_path))

# Add save data directory
if os.path.exists(save_data_path):
    datas.append((save_data_path, os.path.join('Order of the stone', 'save_data')))

# Collect pygame data files
pygame_datas = collect_data_files('pygame')

# Hidden imports for pygame and other modules
hiddenimports = [
    'pygame',
    'pygame.mixer',
    'pygame.mixer_music',
    'pygame.image',
    'pygame.transform',
    'pygame.font',
    'pygame.draw',
    'pygame.event',
    'pygame.key',
    'pygame.mouse',
    'pygame.time',
    'pygame.display',
    'pygame.surface',
    'pygame.rect',
    'pygame.color',
    'pygame.locals',
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'PIL.ImageFont',
    'socket',
    'threading',
    'json',
    'pickle',
    'time',
    'random',
    'math',
    'os',
    'sys',
    'signal',
    'logging'
]

# Analysis configuration
a = Analysis(
    [main_script_path],
    pathex=[current_dir],
    binaries=[],
    datas=datas + pygame_datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Remove duplicate entries
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Create executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Order_of_the_Stone_Demo',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep console for debugging
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
    version=None,
)
