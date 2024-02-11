
import os
import sys
import subprocess
import ctypes
import shutil

pyenv = os.path.join(os.path.dirname(__file__), 'pyenv')
os.makedirs(pyenv, exist_ok=True)
sys.path.append(pyenv)

try:
  from linetimer import CodeTimer
except:
  subprocess.run([
    sys.executable, '-m', 'pip', 'install', f'--target={pyenv}', 'linetimer'
  ])
  from linetimer import CodeTimer

if os.name == 'nt':
  if not 'bin/filegdb_api_vs2013_1_4/bin' in os.environ.get('LD_LIBRARY_PATH', ''):
    print('Re-launching with bin/filegdb_api_vs2013_1_4/bin in LD_LIBRARY_PATH')
    subp_env = dict(os.environ)
    subp_env['PATH'] = os.path.abspath('bin/filegdb_api_vs2013_1_4/bin')+';'+os.environ.get('PATH', '')
    subp_env['LD_LIBRARY_PATH'] = os.path.abspath('bin/filegdb_api_vs2013_1_4/bin')+';'+os.environ.get('LD_LIBRARY_PATH', '')
    p = subprocess.run([sys.executable]+sys.argv, env=subp_env)
    sys.exit(p.returncode)
else:
  if not 'bin/FileGDB_API-64/lib' in os.environ.get('LD_LIBRARY_PATH', ''):
    print('Re-launching with bin/FileGDB_API-64/lib in LD_LIBRARY_PATH')
    subp_env = dict(os.environ)
    subp_env['PATH'] = os.path.abspath('bin/FileGDB_API-64/lib')+':'+os.environ.get('PATH', '')
    subp_env['LD_LIBRARY_PATH'] = os.path.abspath('bin/FileGDB_API-64/lib')+':'+os.environ.get('LD_LIBRARY_PATH', '')
    p = subprocess.run([sys.executable]+sys.argv, env=subp_env)
    sys.exit(p.returncode)


TARGET=None
ENICE_LIB=None
if os.name == 'nt':
  TARGET = 'x86_64-pc-windows-gnu'
  ENICE_LIB = 'enice.dll'
else:
  TARGET = 'x86_64-unknown-linux-gnu'
  ENICE_LIB = 'libenice.so'

def cmd(*args, check=True, cwd=None):
  print(f'>>> {" ".join(args)}')
  subprocess.run([x for x in args if x is not None], check=check, cwd=cwd)


def ensure_native_lib_built():
  cmd(
    'cargo', 'build', '--release', f'--target={TARGET}', cwd='enice'
  )

def ensure_esri_lib():
  os.makedirs('bin', exist_ok=True)
  if os.name == 'nt':
    if not os.path.exists('bin/filegdb_api_vs2013_1_4'):
      raise Exception('\nPlease locate, download, and extract filegdb_api_vs2013_1_4 to bin/filegdb_api_vs2013_1_4 (see https://appsforms.esri.com/products/download/index.cfm?fuseaction=#File_Geodatabase_API_1.4 or https://github.com/Esri/file-geodatabase-api/tree/master/FileGDB_API_1.5.2 )\n')
  else:
    if not os.path.exists('bin/FileGDB_API-64'):
      raise Exception('\nPlease locate, download, and extract FileGDB_API-64 to bin/FileGDB_API-64 (see https://appsforms.esri.com/products/download/index.cfm?fuseaction=#File_Geodatabase_API_1.4 or https://github.com/Esri/file-geodatabase-api/tree/master/FileGDB_API_1.5.2 )\n')


def clean_test_data():
  if os.path.exists('out'):
    shutil.rmtree('out')

def run_tests():
  os.makedirs('out', exist_ok=True)

  lib_enice = ctypes.CDLL(f'enice/target/{TARGET}/release/{ENICE_LIB}')

  with CodeTimer('Enice geodatabase creation'):
    pass

  lib_esri = None
  if os.name == 'nt':
    lib_esri = ctypes.CDLL(f'bin/filegdb_api_vs2013_1_4/bin/FileGDBAPI.dll')
  else:
    lib_esri = ctypes.CDLL(f'bin/FileGDB_API-64/lib/libFileGDBAPI.so')

  with CodeTimer('Esri geodatabase creation'):
    CreateGeodatabase_fn = lib_esri._ZN10FileGDBAPI17CreateGeodatabaseERKSbIwSt11char_traitsIwESaIwEERNS_11GeodatabaseE
    # string to .gdb file, pointer going out to an allocated Geodatabase class
    CreateGeodatabase_fn.argtypes = (ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p))
    CreateGeodatabase_fn.restype = None

    geodatabase_class = ctypes.c_byte * 1024 # No idea how big the class is, but 1kb sounds ok?
    geodatabase_class_memory = geodatabase_class()
    CreateGeodatabase_fn('out/Esri.gdb', ctypes.cast(geodatabase_class_memory, ctypes.POINTER(ctypes.c_void_p) ) )




def main(args=sys.argv):
  print(f'Targeting {TARGET}')
  ensure_native_lib_built()
  ensure_esri_lib()
  clean_test_data()
  run_tests()


if __name__ == '__main__':
  main()
