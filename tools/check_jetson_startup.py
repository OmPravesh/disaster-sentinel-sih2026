import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.50', username='om', password='gtaomp23', timeout=10)

stdin, stdout, stderr = ssh.exec_command("systemctl status sentinel.service | head -n 15")
print("=== sentinel.service status ===")
print(stdout.read().decode('utf-8', 'replace'))

stdin, stdout, stderr = ssh.exec_command("curl -s http://127.0.0.1:5000/api/nodes | head -c 200")
print("=== Dashboard /api/nodes probe ===")
print(stdout.read().decode('utf-8', 'replace'))

stdin, stdout, stderr = ssh.exec_command("ls /dev/ttyUSB* 2>&1")
print("\n=== Connected USB Nodes ===")
print(stdout.read().decode('utf-8', 'replace'))

ssh.close()

