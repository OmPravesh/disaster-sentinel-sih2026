import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("192.168.1.50", username="om", password="gtaomp23")

def run(cmd):
    print(">>> " + cmd)
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode()
    err = stderr.read().decode()
    if out:
        print(out)
    if err:
        print("[ERR] " + err)

run("echo gtaomp23 | sudo -S grep -i pinmux /proc/iomem")
run("zcat /proc/config.gz 2>/dev/null | grep -E 'DEVMEM|PINCTRL_TEGRA' || true")
run("ls -la /sys/bus/platform/drivers/tegra234-pinctrl/ /sys/kernel/debug/pinctrl/2430000.pinmux/")

ssh.close()
