# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(['D:\\Visual Studio\\Python\\Steam Discount Information Getter\\Steam Discount Information Getter\\Steam Discount Information Getter.py'],
             pathex=['D:\\Visual Studio\\Python\\Steam Discount Information Getter'],
             binaries=[],
             datas=[],
             hiddenimports=[],
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
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='Steam Discount Information Getter',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True , icon='D:\\Visual Studio\\Python\\Steam Discount Information Getter\\Steam Discount Information Getter\\Steam Discount Information Getter.ico')
