"""
Disaster Sentinel — Serial Telemetry Bridge
═══════════════════════════════════════════════════════════
Bridges live USB serial output from ESP32 field nodes
directly into the Central Command Dashboard (Port 5000)
and the PyTorch GRU Real-Time AI Engine.

Usage:
  python tools/serial_bridge.py
  python tools/serial_bridge.py --port COM5 --url http://192.168.1.50:5000
═══════════════════════════════════════════════════════════
"""

import sys
import re
import time
import argparse
import urllib.request
import json

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("[ERROR] pyserial is required. Install via: pip install pyserial")
    sys.exit(1)


def find_default_port():
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if "CP210" in p.description or "CH340" in p.description or "USB" in p.description:
            return p.device
    if ports:
        return ports[0].device
    return "COM5"


def parse_and_forward(line: str, api_url: str):
    line = line.strip()
    if not line:
        return

    payload = None

    # Pattern for POL4: "📡 POL4 Sent: AQI=142.5 (L1=0.37), PM2.5=108.3 (L2=0.56) | Combined=0.45"
    m = re.search(r"POL4\s+Sent:\s+AQI=([\d.]+).*?PM2\.5=([\d.]+).*?Combined=([\d.]+)", line)
    if m:
        payload = {
            "node_id": "POL4",
            "l1_raw": float(m.group(1)),
            "l2_raw": float(m.group(2)),
            "l3_raw": 0.0,
            "combined_score": float(m.group(3)),
            "battery": 87,
            "rssi": -68
        }

    # Pattern for FIR3: "📡 FIR3 Sent: Flame=0.00, Gas=0.29, Temp=29.9°C | Combined=0.07"
    m = re.search(r"FIR3\s+Sent:\s+Flame=([\d.]+),\s+Gas=([\d.]+),\s+Temp=([\d.]+)°C.*?Combined=([\d.]+)", line)
    if m:
        payload = {
            "node_id": "FIR3",
            "l1_raw": float(m.group(1)),
            "l2_raw": float(m.group(2)),
            "l3_raw": float(m.group(3)),
            "combined_score": float(m.group(4)),
            "battery": 92,
            "rssi": -65
        }

    # Pattern for SLD2: "📡 SLD2 Sent: Tilt=1.5°, Soil=36.4%, Press=1013.2hPa | Combined=0.00"
    m = re.search(r"SLD2\s+Sent:\s+Tilt=([\d.]+)°,\s+Soil=([\d.]+)%,\s+Press=([\d.]+)hPa.*?Combined=([\d.]+)", line)
    if m:
        payload = {
            "node_id": "SLD2",
            "l1_raw": float(m.group(1)),
            "l2_raw": float(m.group(2)),
            "l3_raw": float(m.group(3)),
            "combined_score": float(m.group(4)),
            "battery": 89,
            "rssi": -72
        }

    # Pattern for FLD1: "[LoRa TX] Packet #1 sent | Node: FLD1 ... L1=300.0(a0) L2=1.0(a0) L3=981.2(a0)"
    m = re.search(r"Node:\s*FLD1.*?L1=([\d.]+).*?L2=([\d.]+).*?L3=([\d.]+)", line)
    if m:
        payload = {
            "node_id": "FLD1",
            "l1_raw": float(m.group(1)),
            "l2_raw": float(m.group(2)),
            "l3_raw": float(m.group(3)),
            "combined_score": 0.0,
            "battery": 95,
            "rssi": -68
        }

    if payload:
        try:
            target_url = f"{api_url.rstrip('/')}/api/telemetry"
            req = urllib.request.Request(
                target_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                status = result.get("status", "OK")
                fc = result.get("forecast", {})
                lead = fc.get("lead_time_label", "") if fc else ""
                print(f"  [SYNCED -> DASHBOARD] {payload['node_id']} | Status: {status} | AI: {lead}")
        except Exception as e:
            print(f"  [WARN] Failed to post to dashboard: {e}")


def main():
    parser = argparse.ArgumentParser(description="Disaster Sentinel Serial Bridge")
    parser.add_argument("--port", default=None, help="Serial port (e.g. COM5 or /dev/ttyUSB0)")
    parser.add_argument("--baud", type=int, default=115200, help="Serial baud rate")
    parser.add_argument("--url", default="http://localhost:5000", help="Web dashboard URL")
    args = parser.parse_args()

    port = args.port or find_default_port()

    print("═══════════════════════════════════════════════════════════")
    print("  DISASTER SENTINEL — LIVE SERIAL-TO-DASHBOARD BRIDGE")
    print("═══════════════════════════════════════════════════════════")
    print(f"  Port:      {port}")
    print(f"  Baud:      {args.baud}")
    print(f"  Dashboard: {args.url}")
    print("  Listening for live sensor packets...\n")

    try:
        ser = serial.Serial(port, args.baud, timeout=1)
    except Exception as e:
        print(f"[ERROR] Could not open serial port {port}: {e}")
        return

    while True:
        try:
            raw_line = ser.readline()
            if raw_line:
                line = raw_line.decode("utf-8", errors="replace")
                sys.stdout.write(line)
                sys.stdout.flush()
                parse_and_forward(line, args.url)
        except KeyboardInterrupt:
            print("\nBridge stopped by user.")
            break
        except Exception as e:
            time.sleep(0.5)


if __name__ == "__main__":
    main()

