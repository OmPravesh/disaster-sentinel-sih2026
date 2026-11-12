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

# Check curl call to server.py to turn buzzer ON
run("curl -X POST http://127.0.0.1:5000/api/actuators/buzzer/on")
# Check actuator status
run("curl http://127.0.0.1:5000/api/actuators")

ssh.close()
