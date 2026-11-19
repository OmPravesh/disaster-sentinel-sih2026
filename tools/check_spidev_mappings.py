from jetson_config import get_jetson_ssh

ssh, ip = get_jetson_ssh()
cmd = "ls -l /sys/class/spidev/"
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
ssh.close()
