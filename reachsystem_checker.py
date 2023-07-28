from django.http import HttpRequest, HttpResponse,  JsonResponse
from django.views.decorators.csrf import csrf_exempt

import json
import os
import psutil
import re
import subprocess
import sys
import time

with open("/root/reachedge_connect/dpdk_supported_nics.json", "r") as f:
    supported_nics = json.load(f)
def nic_driver_check():
  out = subprocess.check_output("lspci -v | grep -A 15 Ethernet", shell=True).decode()
  with open ("nic.txt", "w") as f:
    f.write(out)

  out1 = subprocess.check_output(["awk", "/Ethernet controller:/ {print  $4} /Kernel modules:/ {print $3}", "nic.txt"]).decode()
  out2 = out1.split("\n")
  j=0
  data=[]
  supported_nic = 0
  list_len = int(len(out2)/2)
  for i in range(list_len):
    k = 0
    for m in supported_nics:
      if out2[j+1] in supported_nics[m]:
        k = 1
        supported_nic +=1
        colect = {"manufacturer_name":out2[j], "driver":out2[j+1], "supported": "yes"}
    
 
    if k == 0:
      colect = {"manufacturer_name":out2[j], "driver":out2[j+1], "supported":"not"}
     
    data.append(colect)
    j=j+2
  return data

def hard_check_sse42():
        """Check SSE 4.2 support.

        :param supported:       Unused.

        :returns: 'True' if supported and 'False' otherwise.
        """
        try:
            ret = os.system('cat /proc/cpuinfo | grep sse4_2 > /dev/null 2>&1')
            return ret == 0
        except:
            return False

def hard_check_ram(gb):
        """Check RAM requirements.

        :param gb:       Minimum RAM size in GB.

        :returns: 'True' if check is successful and 'False' otherwise.
        """
        ram = psutil.virtual_memory().total
        ram_gb = ram / pow(1024, 3)
        if psutil.virtual_memory().total < gb * pow(1000, 3):  # 1024^3 might be too strict if some RAM is pre-allocated for VM
            return False
        return ram_gb

def hard_check_cpu_number(num_cores):
        """Check CPU requirements.

        :param num_cores:       Minimum CPU cores number.

        :returns: 'True' if check is successful and 'False' otherwise.
        """
        if psutil.cpu_count() < num_cores:
            return False
        return psutil.cpu_count()

def hard_check_nic_number(num_nics):
        """Check NICs number.

        :param num_nics:       Minimum NICs number.

        :returns: 'True' if check is successful and 'False' otherwise.
        """
        try:
            # NETWORK_BASE_CLASS = "02", so look for 'Class:  02XX'
            out = subprocess.check_output("lspci -Dvmmn | grep -cE 'Class:[[:space:]]+02'", shell=True).decode().strip()
            if int(out) < num_nics:
                return False
        except subprocess.CalledProcessError:
            return False
        return int(out)

def hard_check_kernel_io_modules():
        """Check kernel IP modules presence.

        :param supported:       Unused.

        :returns: 'True' if check is successful and 'False' otherwise.
        """
        modules = [
            # 'uio_pci_generic',  # it is not supported on Amazon, and it is not required as we use 'vfio-pci'
            'vfio-pci'
        ]
        succeeded = True
        for mod in modules:
            ret = os.system(f'modinfo {mod} > /dev/null 2>&1')
            if ret:
                out = subprocess.check_output(f'find /lib/modules -name modules.builtin -exec grep {mod} {{}} \;', shell=True)
                if not out:
                    log.error(mod + ' not found')
                    succeeded = False
        return succeeded


gb = 4
num_cores = 2
num_nics = 2


def hard_checker(request: HttpRequest):
  data=[]
  status_sse = hard_check_sse42()
  if status_sse ==  False:
    print("Instruction set is not supported by processor")
   
  status_ram = hard_check_ram(gb)
  if status_ram ==  False:
    print("Minimum RAM should be 4GB so, Upgrade your RAM")
    
  status_core = hard_check_cpu_number(num_cores)
  if status_core ==  False:
    print("Processor is not supported")
   
  status_nic = hard_check_nic_number(num_nics)
  if status_nic ==  False:
    print("Minimum 2 NIC's required")
    
  status_kernel = hard_check_kernel_io_modules()
  if status_kernel ==  False:
    print("Load the necessary kernel module")
   
  status_driver = nic_driver_check()
  if len(status_driver) < 2:
    print("NIC is not supported")
    
  data.append( {  "instruction_set_compatible":status_sse, 
            "ram":round(status_ram),
            "no_of_cpu_core":status_core,
            "no_of_nic":status_nic,
            "kernel_module_supported":status_kernel, 
            "nic_driver_info":status_driver
          })
          
  return JsonResponse(data, safe=False)
  
@csrf_exempt
def reach_install(request: HttpRequest):
  
  command = "sudo cp -r /home/cloud/reachedge_install /root/reachedge_connect/reachedge_install"
  subprocess.run(command.split())
  os.chdir("/root/reachedge_connect/reachedge_install")
  command = "sudo python3 reachstart.py"
  subprocess.run(command.split())
  os.system("cp /root/reachedge_connect/reachedge_install/vxlan_files/* /root/reachedge_connect/reachwan/")
  os.system("cp /root/reachedge_connect/reachedge_install/vxlan_files/main.py /root/reachedge_connect/reachwan/reachedge/views.py")
  os.system("cp /root/reachedge_connect/reachedge_install/vxlan_files/urls.py /root/reachedge_connect/reachwan/reachwan/urls.py")
  data = {"message":"ReachEdge-install successfull"}
  return JsonResponse(data, safe=False)
  