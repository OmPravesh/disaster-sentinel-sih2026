import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.50', username='om', password='gtaomp23', timeout=10)

stdin, stdout, stderr = ssh.exec_command("grep -n \"Hardware Bus Discovery\" /tmp/serial_bridge.log | tail -n 5")
print("Discovery matches:")
print(stdout.read().decode('utf-8', 'replace'))

stdin, stdout, stderr = ssh.exec_command("grep -A 20 \"Hardware Bus Discovery\" /tmp/serial_bridge.log | tail -n 25")
print("Discovery details:")
print(stdout.read().decode('utf-8', 'replace'))

ssh.close()

