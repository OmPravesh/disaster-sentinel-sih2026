import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.50', username='om', password='gtaomp23')

# Check if serial_bridge is running
stdin, stdout, stderr = ssh.exec_command('ps aux | grep serial_bridge')
print("Active serial_bridge processes:")
print(stdout.read().decode())

# Check journalctl for sentinel.service (LoRa receiver)
stdin, stdout, stderr = ssh.exec_command('journalctl -u sentinel.service -n 20 --no-pager')
print("Sentinel service recent logs:")
print(stdout.read().decode())

ssh.close()

