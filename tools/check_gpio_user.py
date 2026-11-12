import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.50', username='om', password='gtaomp23', timeout=10)

stdin, stdout, stderr = ssh.exec_command("""
/home/om/venv/bin/python - << 'EOF'
import os
os.environ["JETSON_MODEL_NAME"] = "JETSON_ORIN_NANO"
try:
    import Jetson.GPIO as GPIO
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(12, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(16, GPIO.OUT, initial=GPIO.LOW)
    print("SUCCESS: User om can control Jetson.GPIO without sudo!")
except Exception as e:
    print("FAILED:", e)
EOF
""")

print(stdout.read().decode('utf-8', 'replace'))
print(stderr.read().decode('utf-8', 'replace'))
ssh.close()

