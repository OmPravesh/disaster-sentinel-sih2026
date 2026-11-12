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

run("echo gtaomp23 | sudo -S cat /sys/kernel/debug/gpio | grep -E 'PH.07|PY.04|Jetson-gpio|398|474'")
run("gpioinfo | grep -B2 -A2 'Jetson-gpio'")
run("python3 -c 'import os; os.environ[\"JETSON_MODEL_NAME\"]=\"JETSON_ORIN_NANO\"; import Jetson.GPIO as G; from Jetson.GPIO import gpio_pin_data; print(gpio_pin_data.get_data())'")

ssh.close()

