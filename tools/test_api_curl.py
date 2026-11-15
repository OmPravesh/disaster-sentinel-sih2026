import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("192.168.1.50", username="om", password="gtaomp23")
stdin, stdout, stderr = ssh.exec_command("curl -s -X POST http://127.0.0.1:5000/api/actuators/all/off")
print(stdout.read().decode())
ssh.close()
