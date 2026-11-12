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

run("echo gtaomp23 | sudo -S cat /sys/kernel/debug/pinctrl/2430000.pinmux/pinconf-groups | grep -A 12 -E 'ph7|py4|pg6|pr5|pq5|pq6|pn1|pac6|pr4'")
run("echo gtaomp23 | sudo -S cat /sys/kernel/debug/pinctrl/c300000.pinmux/pinconf-groups | grep -A 12 -E 'pcc4'")

ssh.close()

