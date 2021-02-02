# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

pathex = os.path.abspath(SPECPATH)


a = Analysis(['src/main.py'],
             pathex=[pathex],
             binaries=[],
             datas=[(os.path.join(pathex, 'ui'), 'ui')],
             hiddenimports=['plugins.plugin_header'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='AMP',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='AMP')
app = BUNDLE(coll,
             name='AMP.app',
             icon=None,
             bundle_identifier=None)
