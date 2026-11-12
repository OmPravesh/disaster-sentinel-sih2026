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

run("echo gtaomp23 | sudo -S cat /sys/kernel/debug/gpio | grep -E 'PH.07|PY.04'")
run("echo gtaomp23 | sudo -S cat /sys/kernel/debug/pinctrl/2430000.pinmux/pinconf-groups | grep -A 5 -E 'soc_gpio41_ph7|spi3_cs1_py4'")
run("systemctl --version")

ssh.close()

