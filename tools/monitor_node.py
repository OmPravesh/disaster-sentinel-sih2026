"""
Disaster Sentinel — Real-Time ESP32 Serial & Sensor Monitor
=============================================================
Streams live hardware diagnostics from the ESP32 (/dev/ttyUSB0)
over SSH directly to your Windows laptop terminal in real time.

Usage:
    python tools/monitor_node.py
"""

import sys
import time
import paramiko

JETSON_IP = "192.168.1.50"
JETSON_USER = "om"
JETSON_PASS = "gtaomp23"

# ANSI colors for Windows terminal
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

def main():
    print(f"\n{BOLD}{CYAN}==========================================================={RESET}")
    print(f"{BOLD}{CYAN}  DISASTER SENTINEL — LIVE HARDWARE SENSOR MONITOR{RESET}")
    print(f"{BOLD}{CYAN}  Connecting to ESP32 on Jetson ({JETSON_IP})...{RESET}")
    print(f"{BOLD}{CYAN}  Press Ctrl+C to stop.{RESET}")
    print(f"{BOLD}{CYAN}==========================================================={RESET}\n")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(JETSON_IP, username=JETSON_USER, password=JETSON_PASS, timeout=10)
    except Exception as e:
        print(f"{RED}❌ Could not connect to Jetson at {JETSON_IP}: {e}{RESET}")
        return

    # Run tail -f on the serial bridge log
    stdin, stdout, stderr = ssh.exec_command("tail -n 20 -f /tmp/serial_bridge.log", get_pty=True)

    try:
        for line in iter(stdout.readline, ""):
            line = line.strip()
            if not line:
                continue

            # Format with colors for clear reading
            if "Tilt=" in line:
                # Highlight tilt and soil readings
                print(f"{GREEN}{BOLD}📡 {line}{RESET}", flush=True)
            elif "I2C PROBE" in line or "I2C STATUS" in line or "I2C LIVE SCAN" in line:
                print(f"{YELLOW}🔍 {line}{RESET}", flush=True)
            elif "RAW MPU" in line or "MPU INITIALIZED" in line:
                print(f"{CYAN}{BOLD}🎯 {line}{RESET}", flush=True)
            elif "Synced to Dashboard" in line:
                print(f"  {line}", flush=True)
            elif "ERROR" in line or "Failed" in line or "err2" in line:
                print(f"{RED}{line}{RESET}", flush=True)
            else:
                print(f"  {line}", flush=True)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Stopping monitor...{RESET}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
