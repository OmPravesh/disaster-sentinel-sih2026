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

run("dtc -I dtb -O dts /boot/jetson-io-hdr40-user-custom.dtbo 2>/dev/null || true")
run("echo gtaomp23 | sudo -S cat /sys/kernel/debug/pinctrl/2430000.pinmux/pinmux-pins | grep -E 'PH7|PY4|PG6|PR5|PQ5|PQ6|PCC4|PN1|PZ6|PZ7|PAC6|soc_gpio|i2s|spi3|pwm'")
run("echo gtaomp23 | sudo -S cat /sys/kernel/debug/pinctrl/c300000.pinmux/pinmux-pins | grep -E 'PCC4|soc_gpio'")

ssh.close()
