import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.50', username='om', password='gtaomp23', timeout=10)

stdin, stdout, stderr = ssh.exec_command("""
/home/om/venv/bin/python - << 'EOF'
import os
os.environ["JETSON_MODEL_NAME"] = "JETSON_ORIN_NANO"
import Jetson.GPIO as GPIO
data = GPIO.gpio_pin_data.get_data()
channels = data[2]
print("data[2] type:", type(channels))
for k, v in list(channels.items())[:10]:
    print(k, "->", v)
EOF
""")

print(stdout.read().decode('utf-8', 'replace'))
print(stderr.read().decode('utf-8', 'replace'))
ssh.close()
