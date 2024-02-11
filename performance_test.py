
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
  pass # todo

def clean_test_data():
  if os.path.exists('out'):
    shutil.rmtree('out')

def run_tests():
  os.makedirs('out', exist_ok=True)

  lib_enice = ctypes.CDLL(f'enice/target/{TARGET}/release/{ENICE_LIB}')

  with CodeTimer('Enice geodatabase creation'):
    pass

  #lib_esri = ctypes.CDLL(f'enice/target/{TARGET}/release/')

  with CodeTimer('Esri geodatabase creation'):
    pass


def main(args=sys.argv):
  print(f'Targeting {TARGET}')
  ensure_native_lib_built()
  ensure_esri_lib()
  clean_test_data()
  run_tests()


if __name__ == '__main__':
  main()
