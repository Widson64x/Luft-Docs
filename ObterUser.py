import os
import getpass
import socket
import subprocess

# Executa o comando WMIC para obter o serial
serial = subprocess.check_output("wmic bios get serialnumber", shell=True).decode().split("\n")[1].strip()

# Usuário e domínio
usuario = getpass.getuser()
dominio = os.environ.get('USERDOMAIN')

# Nome da máquina
hostname = socket.gethostname()

# IP da máquina
ip = socket.gethostbyname(hostname)

print(f"Domínio: {dominio}")
print(f"Usuário: {usuario}")
print(f"Computador: {hostname}c")
print(f"IP: {ip}")
print(f"Serial da máquina: {serial}")