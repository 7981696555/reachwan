import os
import subprocess
import time


req_apt_packages = ["net-tools", "pip", "openvpn", "isc-dhcp-server", "network-manager"]
req_pip_packages = ["pymongo", "flask", "flask-cors", "psutil", "netaddr", "pyroute2", "django"]
req_ports = ["1194/udp", "5000", "500/esp", "4789/udp", "27017/tcp", "89", "53", "22", "67/udp", "179/tcp"]


def run_command(command):
  subprocess.run(command.split())
  

def install_req_apt_packages(packages):
    try:
      command = (f"sudo apt-get install -y {packages}")
      out = subprocess.check_output(command.split()).decode()
    
    except subprocess.CalledProcessError:
      print("Error while installing please check your internet connection")
      exit()
    
def install_req_pip_packages(packages):
    try:
      command = (f"sudo pip install {packages}")
      out = subprocess.check_output(command.split()).decode()
      
    except subprocess.CalledProcessError:
      print("Error while installing please check your internet connection")
      exit()
       
def pip_packages():
  for package in req_pip_packages:
    status = install_req_pip_packages(package)
    
def apt_packages():
  for package in req_apt_packages:
    status = install_req_apt_packages(package)
    

def enable_ports():
  for ports in req_ports:
    command = (f"sudo ufw allow {ports}")
    subprocess.run(command.split())
  return True
  
   
def openvpn_config():
  try:
    command  = "sudo cp client.conf /etc/openvpn/client.conf"
    subprocess.check_output(command.split())
    command = "sudo systemctl start openvpn@client"
    subprocess.check_output(command.split())
    command = "sudo systemctl daemon-reload"
    subprocess.check_output(command.split())
    command = "sudo systemctl restart openvpn@client"
    subprocess.check_output(command.split()).decode()
    
  except subprocess.CalledProcessError:
    print("error while configuring openvpn client")
    exit()
  return True   
  
def create_new_user(username, password):
    try:
        # Create the new user with the specified username
        subprocess.run(['sudo', 'useradd', '-m', username], check=True)
        command =f"openssl passwd -1 {password}"
        out = subprocess.check_output(command.split()).decode()
        out1 = out.split("\n")[0]
        # Set the password for the new user
        subprocess.run(['sudo', 'usermod', '-p', out1, username], check=True)

        print(f"User '{username}' created successfully.")
        command2 = f"usermod -aG sudo {username}"
        subprocess.run(command2.split())
        with open("/etc/ssh/sshd_config", "a") as f:
          f.write(f"\nPermitRootLogin yes\nPasswordAuthentication yes\nAllowUsers {username}\n")
        subprocess.run(["sudo", "service", "ssh", "restart"])
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print("Failed to create the user. Please check if you have sudo privileges.")

def database_install():
  try:  
    subprocess.run(['sudo', 'apt-get', 'install', 'gnupg'])
    subprocess.run(['curl', '-fsSL', 'https://pgp.mongodb.com/server-6.0.asc', '|', 'sudo', 'gpg', '-o', '/usr/share/keyrings/mongodb-server-6.0.gpg', '--dearmor'])
    with open('/etc/apt/sources.list.d/mongodb-org-6.0.list', 'w') as f:
      f.write('deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-6.0.gpg ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse\n')
    subprocess.run(['sudo', 'tee', '/etc/apt/sources.list.d/mongodb-org-6.0.list'], input=b"deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-6.0.gpg ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse\n", check=True)
    subprocess.run(['sudo', 'apt-get', 'update'])
    subprocess.run(['sudo', 'apt-get', 'install', '-y', 'mongodb'])
    subprocess.run(['sudo', 'systemctl', 'enable', 'mongodb'])
    subprocess.run(['sudo', 'systemctl', 'start', 'mongodb'])
    subprocess.run(['sudo', 'systemctl', 'daemon-reload'])
    subprocess.run(['sudo', 'systemctl', 'enable', 'mongodb'])
  except subprocess.CalledProcessError:
    os.system("sudo rm -r /etc/apt/sources.list.d/mongodb-org-6.0.list")
    database_install()
    
def main():
  subprocess.run(['sudo', 'apt', 'update'])
  print("apt update completed")
  apt_packages()
  print("apt completed")
  pip_packages()
  enable_ports()
  database_install()
  print("ports completed")
  new_username = "cloud"  # Replace with the desired username
  new_password = "cloud23"  # Replace with the desired password
  create_new_user(new_username, new_password)
  print("user created completed")
  openvpn_config()
  subprocess.run(["sudo", "django-admin", "startproject", "reachwan"])
  os.chdir("reachwan")
  os.system("sudo python3 manage.py startapp reachedge")
  os.chdir("..")
  with open("/root/reachedge_connect/reachwan/reachwan/settings.py", "r") as f:
    data1 = f.read()
  data1 = data1.replace("ALLOWED_HOSTS = []", "ALLOWED_HOSTS = ['*']")
  data1 = data1.replace("MIDDLEWARE = [", 'MIDDLEWARE = [ "reachwan.restrict_ip_middleware.RestrictIPMiddleware",')
  with open("/root/reachedge_connect/reachwan/reachwan/settings.py", "w") as f:
    f.write(data1)
  os.system("cp restrict_ip_middleware.py reachwan/reachwan/restrict_ip_middleware.py")
  os.system("cp reachsystem_checker.py reachwan/reachedge/views.py")
  
  os.system("cp urls.py reachwan/reachwan/urls.py")
  os.chdir("reachwan")
  subprocess.run(['sudo', 'python3', 'manage.py', 'runserver', '0.0.0.0:5000'])

main()