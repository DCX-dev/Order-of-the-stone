# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['Order of the stone/assets/com/dreamcrusherx/Order of the stone/main_script/order_of_the_stone.py'],
    pathex=['Order of the stone/assets/com/dreamcrusherx/Order of the stone'],
    binaries=[],
    datas=[('Order of the stone/assets', 'assets'), ('Order of the stone/damage', 'damage'), ('Order of the stone/assets/com/dreamcrusherx/Order of the stone/ui', 'ui'), ('Order of the stone/assets/com/dreamcrusherx/Order of the stone/system', 'system'), ('Order of the stone/assets/com/dreamcrusherx/Order of the stone/managers', 'managers')],
    hiddenimports=['ui.modern_ui', 'ui.world_ui', 'ui.multiplayer_ui', 'system.world_system', 'system.chest_system', 'system.chat_system', 'managers.character_manager', 'managers.coins_manager'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pygame.sndarray', 'numpy'],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Order_of_the_Stone.exe',
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
)
app = BUNDLE(
    exe,
    name='Order_of_the_Stone.exe.app',
    icon=None,
    bundle_identifier=None,
)
