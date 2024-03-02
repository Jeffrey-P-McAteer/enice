#!/usr/bin/env python

VM_DATA_DIR = '/mnt/scratch/vms/enice-win11'

import os
import sys
import subprocess
import shutil
import time
import zipfile
import traceback
import tarfile
import glob

site_packages = os.path.join(os.path.dirname(__file__), 'site-packages')
os.makedirs(site_packages, exist_ok=True)
sys.path.append(site_packages)

try:
  import selenium
except:
  subprocess.run([
    sys.executable, '-m', 'pip', 'install', f'--target={site_packages}', 'selenium'
  ])
  import selenium


from selenium import webdriver
from selenium.webdriver.firefox.options import Options

from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

def ensure_vm_material_downloaded():
  os.makedirs(VM_DATA_DIR, exist_ok=True)

  vm_zip_file = f'{VM_DATA_DIR}/WinDev2401Eval.VirtualBox.zip'

  if not os.path.exists(vm_zip_file) or os.path.getsize(vm_zip_file) < 10:
    profile = webdriver.FirefoxProfile()
    profile.set_preference('browser.download.folderList', 2)
    profile.set_preference('browser.download.manager.showWhenStarting', False)
    profile.set_preference('browser.download.dir', os.path.abspath(VM_DATA_DIR) )
    profile.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/octet-stream')

    options = Options()
    options.headless = True
    options.profile = profile

    driver = webdriver.Firefox(options=options)

    try:
      driver.get('https://developer.microsoft.com/en-us/windows/downloads/virtual-machines/')
      driver.get('https://aka.ms/windev_VM_virtualbox')
      driver.quit()
    except:
      # usually a timeout
      if 'timeout' in traceback.format_exc():
        pass
      else:
        traceback.print_exc()

    # Poll until os.path.getsize(vm_zip_file) is non-zero
    while True:
      time.sleep(1)
      print('Polling for download to complete')
      if os.path.getsize(vm_zip_file) > 1024:
        break
      time.sleep(9)
    print('Download complete!')


def ensure_vm_created_from_material():
  vm_zip_file = f'{VM_DATA_DIR}/WinDev2401Eval.VirtualBox.zip'
  vm_material_dir = f'{VM_DATA_DIR}/WinDev2401Eval'
  os.makedirs(vm_material_dir, exist_ok=True)

  num_extracted_files = len([x for x in os.listdir(vm_material_dir)])
  if num_extracted_files < 1:
    print(f'Extracting {vm_zip_file} to {vm_material_dir}')
    zip_ref = zipfile.ZipFile(vm_zip_file)
    zip_ref.extractall(vm_material_dir)
    zip_ref.close()

  # Convert files to qcow2
  ova_f = f'{VM_DATA_DIR}/WinDev2401Eval/WinDev2401Eval.ova'
  ova_dir = f'{VM_DATA_DIR}/WinDev2401Eval/WinDev2401Eval'
  os.makedirs(ova_dir, exist_ok=True)
  if len([x for x in os.listdir(ova_dir)]) < 1:
    print(f'Extracting {ova_f} to {ova_dir}')
    tfile = tarfile.open(ova_f)
    tfile.extractall(ova_dir)

  # ova_vmdk_f = 'out/WinDev2401Eval/WinDev2401Eval/WinDev2401Eval-disk001.vmdk'

  vm_qcow2_image = f'{VM_DATA_DIR}/WinDev2401Eval.qcow2'

  if not os.path.exists(vm_qcow2_image) or os.path.getsize(vm_qcow2_image) < 10:
    all_vmdk_files = []
    for vmdk_f in glob.glob(f'{VM_DATA_DIR}/WinDev2401Eval/WinDev2401Eval/*.vmdk'):
      all_vmdk_files.append(vmdk_f)
    print(f'Creating {vm_qcow2_image} from {all_vmdk_files}')
    subprocess.run([
      'qemu-img', 'convert', '-f', 'vmdk', '-O', 'qcow2', *all_vmdk_files, vm_qcow2_image
    ])
    # and finally ensure we allocate about 140 GB for the drive; will need to expand from within the guest as well!
    subprocess.run([
      'qemu-img', 'resize', vm_qcow2_image, '146G'
    ])

  print(f'VM hard drive is at {vm_qcow2_image}')




def boot_vm():

  for i in range(1, 5):
    swapfile = f'/mnt/scratch/swap-files/swap-{i}'
    if os.path.exists(swapfile):
      subprocess.run([
        'sudo', 'swapon', swapfile
      ], check=False)

  vm_qcow2_image = f'{VM_DATA_DIR}/WinDev2401Eval.qcow2'
  shared_folder = os.path.abspath('.')
  print()
  print(f'shared_folder = {shared_folder}')
  #print(r'Access as \\10.0.2.4\qemu within VM')
  print('Release mouse with ctrl+alt+g')
  print()

  cmd = [
    'systemd-run',
      '--scope', '-p', 'MemoryHigh=12G', '-p', 'MemorySwapMax=999G', '--user',

    'qemu-system-x86_64',
      '-bios', '/usr/share/edk2-ovmf/x64/OVMF_CODE.fd',
      '-drive', f'format=qcow2,file={vm_qcow2_image}',
      '-enable-kvm',
      '-m', '12000M',
      '-cpu', 'host',
      '-smp', '2',
      '-machine', 'type=pc,accel=kvm,kernel_irqchip=on',
      #'-nic', f'user,id=winnet0,id=mynet0,net=192.168.90.0/24,dhcpstart=192.168.90.10,hostfwd=tcp::3389-:3389,hostfwd=udp::3389-:3389,smb={shared_folder}',
      '-nic', f'user,id=winnet0,id=mynet0,net=192.168.90.0/24,dhcpstart=192.168.90.10,hostfwd=tcp::3389-:3389,hostfwd=udp::3389-:3389',
      '-net', 'nic,model=virtio',
      '-boot', 'c',

      '-vga', 'virtio',
      '-display', 'gtk,gl=on,show-cursor=on',
      '-usb', '-device', 'usb-kbd', '-device', 'usb-tablet',
  ]

  mytpm = '/tmp/mytpm1'
  if os.path.exists(mytpm):
    cmd += [
      '-chardev', f'socket,id=chrtpm,path={mytpm}/swtpm-sock',
      '-tpmdev', 'emulator,id=tpm0,chardev=chrtpm',
      '-device', 'tpm-tis,tpmdev=tpm0'
    ]
  else:
    print()
    print('''
Please run the following to emulate a TPM, if required.

  mkdir /tmp/mytpm1
  swtpm socket --tpmstate dir=/tmp/mytpm1 \
    --ctrl type=unixio,path=/tmp/mytpm1/swtpm-sock \
    --tpm2 \
    --log level=20

in another terminal.
'''.strip())
    print()

  print()
  print(f'>>> {" ".join(cmd)}')
  print()

  subprocess.run(cmd)

def main():
  ensure_vm_material_downloaded()
  ensure_vm_created_from_material()
  boot_vm()


if __name__ == '__main__':
  main()

