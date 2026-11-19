from jetson_config import get_jetson_ssh

ssh, ip = get_jetson_ssh()
print(f"Connected to Jetson at {ip}")
cmd = "curl -s http://localhost:5000/api/actuators"
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
ssh.close()
