from jetson_config import get_jetson_ssh

ssh, ip = get_jetson_ssh()
cmd = "echo gtaomp23 | sudo -S dmesg | grep -i spi"
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
ssh.close()
