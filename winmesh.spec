# -*- mode: python -*-
import os
import sys
import inspect

base_path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

def make_tree(base_path, subdir):
  path = os.path.join(base_path, subdir)
  prefix = "".join([subdir, "\\"])
  return Tree(path, prefix)

a = Analysis(['winmesh.py'],
             pathex=[base_path],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)

pyz = PYZ(a.pure)

exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='winmesh.exe',
          debug=False,
          strip=None,
          upx=True,
          console=True )

coll = COLLECT(exe,
               make_tree(base_path, 'olsrd'),
               make_tree(base_path, 'images'),
               make_tree(base_path, 'profiles'),
               make_tree(base_path, 'templates'),
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name='winmesh')
