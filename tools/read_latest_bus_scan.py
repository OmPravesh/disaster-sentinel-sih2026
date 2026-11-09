import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.50', username='om', password='gtaomp23', timeout=10)

stdin, stdout, stderr = ssh.exec_command("tail -n 30 /tmp/serial_bridge.log")
output = stdout.read().decode('utf-8', 'replace')
print(output)

ssh.close()

