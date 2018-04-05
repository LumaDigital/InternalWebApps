# -*- mode: python -*-

block_cipher = None

include_files =[ ('config.json', '.') , ('Temperature.ico', '.'), ('StartClient.bat', '.'), ('devcon.exe', '.')]

a = Analysis(['Main.py','Monitor.py','LumaCommServer.py','ProcessManager.py'],
             pathex=['D:\\Repos\\InternalWebApps\\LumaMonitor', 'C:\\Python27\\Lib\\site-packages', 'C:\\Users\\johanvs\\venv\\Lib\\site-packages'],
             binaries=[],
             datas= include_files,
             hiddenimports=['wmi','psutil'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='LumaMonitor',
          debug=False,
          strip=False,
          upx=True,
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='LumaMonitor')
