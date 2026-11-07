import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.50', username='om', password='gtaomp23')

sftp = ssh.open_sftp()
remote_path = '/home/om/disaster-sentinel-sih2026/firmware/node_landslide/.pio/libdeps/esp32dev/Adafruit MPU6050/Adafruit_MPU6050.cpp'
with sftp.open(remote_path, 'r') as f:
    content = f.read().decode('utf-8')

target = 'if (chip_id.read() != MPU6050_DEVICE_ID) {'
replacement = 'uint8_t cid = chip_id.read();\n  if (cid != MPU6050_DEVICE_ID && cid != 0x70 && cid != 0x71 && cid != 0x72 && cid != 0x73) {'

if target in content:
    content = content.replace(target, replacement)
    with sftp.open(remote_path, 'w') as f:
        f.write(content)
    print("SUCCESS: Patched Adafruit_MPU6050.cpp on Jetson!")
else:
    print("Notice: target already replaced or not found")

sftp.close()

_, stdout, _ = ssh.exec_command("sed -n 90,98p '/home/om/disaster-sentinel-sih2026/firmware/node_landslide/.pio/libdeps/esp32dev/Adafruit MPU6050/Adafruit_MPU6050.cpp'")
print("\n--- Verified Lines in Adafruit_MPU6050.cpp ---")
print(stdout.read().decode())

ssh.close()
