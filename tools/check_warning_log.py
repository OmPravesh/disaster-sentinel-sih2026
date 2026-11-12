import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.50', username='om', password='gtaomp23', timeout=10)

stdin, stdout, stderr = ssh.exec_command("grep -n 'setup warning' /tmp/sentinel_server.log")
print("Warning grep:", stdout.read().decode('utf-8', 'replace'))

ssh.close()

