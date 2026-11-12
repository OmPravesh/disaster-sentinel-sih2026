import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.50', username='om', password='gtaomp23', timeout=10)

test_script = '''
import os
os.environ["JETSON_MODEL_NAME"] = "JETSON_ORIN_NANO"
import Jetson.GPIO as GPIO
import time

print("Jetson.GPIO version:", GPIO.VERSION)
print("Jetson model detected:", GPIO.model)

# Test Pin 12 (Physical Pin 12 / BCM 18) for Buzzer
# Test Pin 16 (Physical Pin 16 / BCM 23) for Strobe/Relay

print("\\n--- Testing with GPIO.BOARD (Physical 40-pin header pins) ---")
GPIO.setmode(GPIO.BOARD)

for pin_name, pin_num in [("Buzzer (Header Pin 12)", 12), ("Strobe/Relay (Header Pin 16)", 16)]:
    try:
        GPIO.setup(pin_num, GPIO.OUT, initial=GPIO.LOW)
        print(f"Testing {pin_name} -> TURNING ON (HIGH) for 2 seconds...")
        GPIO.output(pin_num, GPIO.HIGH)
        time.sleep(2)
        GPIO.output(pin_num, GPIO.LOW)
        print(f"Testing {pin_name} -> TURNING OFF (LOW)")
    except Exception as e:
        print(f"Error testing {pin_name}: {e}")

GPIO.cleanup()
print("\\n--- Testing Complete ---")
'''

sftp = ssh.open_sftp()
with sftp.file('/tmp/test_gpio.py', 'w') as f:
    f.write(test_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("echo gtaomp23 | sudo -S /home/om/venv/bin/python /tmp/test_gpio.py")
print(stdout.read().decode('utf-8', 'replace'))
print(stderr.read().decode('utf-8', 'replace'))

ssh.close()

