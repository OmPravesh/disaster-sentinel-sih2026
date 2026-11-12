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

run("ls -d /sys/firmware/devicetree/base/*pinmux* /sys/firmware/devicetree/base/bus@0/*pinmux* 2>/dev/null || true")
run("cat /opt/nvidia/jetson-io/Jetson/pmx.py")

ssh.close()
