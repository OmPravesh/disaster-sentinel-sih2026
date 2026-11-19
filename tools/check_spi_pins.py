from jetson_config import get_jetson_ssh

ssh, ip = get_jetson_ssh()
cmd = """
python3 - << 'EOF'
import subprocess
out = subprocess.check_output(['sudo', 'cat', '/sys/kernel/debug/pinctrl/2430000.pinmux/pinconf-groups'], text=True)
pins = ['spi1', 'spi3', 'spi']
for line in out.splitlines():
    if any(k in line.lower() for k in ['spi1_mosi', 'spi1_miso', 'spi1_sck', 'spi1_cs', 'spi3_cs', 'spi0']):
        print(line)
EOF
"""
stdin, stdout, stderr = ssh.exec_command(f"echo gtaomp23 | {cmd}")
print(stdout.read().decode())
ssh.close()

