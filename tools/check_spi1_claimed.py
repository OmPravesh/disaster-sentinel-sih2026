from jetson_config import get_jetson_ssh

ssh, ip = get_jetson_ssh()
cmd = "echo gtaomp23 | sudo -S cat /sys/kernel/debug/pinctrl/2430000.pinmux/pinmux-pins | grep -i spi1"
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
ssh.close()

