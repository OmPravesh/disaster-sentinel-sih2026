from jetson_config import get_jetson_ssh

ssh, ip = get_jetson_ssh()
cmd = "echo gtaomp23 | sudo -S cat /sys/kernel/debug/pinctrl/2430000.pinmux/pinconf-groups | grep -A 10 -E '79 \(spi1_cs0|81 \(spi1_miso|83 \(spi1_sck|86 \(spi1_mosi'"
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
ssh.close()

