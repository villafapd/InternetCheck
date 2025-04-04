import os

interfaces = ["eth1", "wlan0"]
for interface in interfaces:
    response = os.system(f"ping -c 3 -I {interface} 8.8.8.8 > /dev/null 2>&1")
    if response == 0:
        print(f"Conexion activa: {interface}")
        break
