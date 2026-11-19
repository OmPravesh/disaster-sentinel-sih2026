from jetson_config import get_jetson_ssh

ssh, ip = get_jetson_ssh()
cmd = "echo gtaomp23 | sudo -S cat /sys/kernel/debug/pinctrl/2430000.pinmux/pinconf-groups | grep -E '^[0-9]+ \([a-zA-Z0-9_]+\):' | grep spi"
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
ssh.close()

