"""
Disaster Sentinel — Multi-Node Serial Telemetry Bridge
=====================================================
Bridges live USB serial telemetry from ALL connected ESP32
field nodes simultaneously (via a 4-Port USB 3.0 Hub or individual ports)
directly into the Central Command Dashboard (Port 5000) and the
PyTorch GRU Real-Time AI Early Warning Engine.
"""

import sys
import re
import time
import argparse
import urllib.request
import json
import threading

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("[ERROR] pyserial is required. Install via: pip install pyserial")
    sys.exit(1)


def find_esp32_ports():
    """Detects all serial devices connected (e.g. via 4-port USB hub)."""
    detected = []
    for p in serial.tools.list_ports.comports():
        dev = p.device
        desc = (p.description or "").upper()
        mfg = (p.manufacturer or "").upper()
        hwid = (p.hwid or "").upper()

        if dev.upper() == "COM1":
            continue

        if any(x in desc or x in mfg or x in hwid for x in ["CP210", "CH340", "CH9102", "FTDI", "SILICON LABS", "USB TO UART", "USB-SERIAL", "UART"]):
            detected.append((dev, p.description))
        elif "COM" in dev:
            detected.append((dev, p.description or "Serial Device"))
    return detected


def parse_and_forward(port_name: str, line: str, api_url: str):
    """Parses incoming serial log lines from any of the 4 nodes and posts to dashboard."""
    line = line.strip()
    if not line:
        return

    payload = None

    # 1. Node POL4 (Pollution)
    m_pol = re.search(r"POL4.*?(?:Sent:|Telemetry).*?AQI=([\d.]+).*?PM2\.5=([\d.]+).*?Combined=([\d.]+)", line, re.IGNORECASE)
    if m_pol:
        payload = {
            "node_id": "POL4",
            "l1_raw": float(m_pol.group(1)),
            "l2_raw": float(m_pol.group(2)),
            "l3_raw": 0.0,
            "combined_score": float(m_pol.group(3)),
            "battery": 88,
            "rssi": -68
        }

    # 2. Node FIR3 (Fire)
    m_fir = re.search(r"FIR3.*?(?:Sent:|Telemetry).*?Flame=([\d.]+).*?Gas=([\d.]+).*?Temp=([\d.]+)°?C.*?Combined=([\d.]+)", line, re.IGNORECASE)
    if m_fir:
        payload = {
            "node_id": "FIR3",
            "l1_raw": float(m_fir.group(1)),
            "l2_raw": float(m_fir.group(2)),
            "l3_raw": float(m_fir.group(3)),
            "combined_score": float(m_fir.group(4)),
            "battery": 92,
            "rssi": -65
        }

    # 3. Node SLD2 (Landslide)
    m_sld = re.search(r"SLD2.*?(?:Sent:|Telemetry).*?Tilt=([\d.]+)°?.*?Soil=([\d.]+)%.*?Press=([\d.]+)hPa.*?Combined=([\d.]+)", line, re.IGNORECASE)
    if m_sld:
        payload = {
            "node_id": "SLD2",
            "l1_raw": float(m_sld.group(1)),
            "l2_raw": float(m_sld.group(2)),
            "l3_raw": float(m_sld.group(3)),
            "combined_score": float(m_sld.group(4)),
            "battery": 89,
            "rssi": -72
        }

    # 4. Node FLD1 (Flood)
    m_fld = re.search(r"Node:\s*FLD1.*?L1=([\d.]+).*?L2=([\d.]+).*?L3=([\d.]+)", line, re.IGNORECASE)
    if m_fld:
        comb_match = re.search(r"Combined:\s*([\d.]+)", line)
        comb_val = float(comb_match.group(1)) if comb_match else 0.0
        bat_match = re.search(r"Bat:\s*(\d+)%", line)
        bat_val = int(bat_match.group(1)) if bat_match else 95

        payload = {
            "node_id": "FLD1",
            "l1_raw": float(m_fld.group(1)),
            "l2_raw": float(m_fld.group(2)),
            "l3_raw": float(m_fld.group(3)),
            "combined_score": comb_val,
            "battery": bat_val,
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
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                status = result.get("status", "OK")
                fc = result.get("forecast", {})
                lead = fc.get("lead_time_label", "") if fc else ""
                ai_info = f" | AI: {lead}" if lead else ""
                print(f"  [{port_name} ➔ {payload['node_id']}] Synced to Dashboard! | Status: {status}{ai_info}")
        except Exception as e:
            print(f"  [{port_name} ➔ {payload['node_id']}] Sync warning: {e}")


def listen_port(port_name: str, baud: int, api_url: str, stop_event: threading.Event):
    """Worker thread listening to a single COM port."""
    try:
        ser = serial.Serial(port_name, baud, timeout=1)
        print(f"  [CONNECTED] {port_name} @ {baud} baud")
    except Exception as e:
        print(f"  [ERROR] Could not open {port_name}: {e}")
        return

    try:
        while not stop_event.is_set():
            try:
                raw_line = ser.readline()
                if raw_line:
                    line = raw_line.decode("utf-8", errors="replace").strip()
                    if line:
                        if any(k in line for k in ["Sent:", "Node:", "LoRa", "Telemetry", "DISASTER", "Combined="]):
                            print(f"[{port_name}] {line}")
                        parse_and_forward(port_name, line, api_url)
            except serial.SerialException:
                print(f"  [DISCONNECTED] {port_name} was unplugged.")
                break
            except Exception:
                time.sleep(0.1)
    finally:
        try:
            ser.close()
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser(description="Disaster Sentinel Multi-Node Serial Bridge")
    parser.add_argument("--port", default=None, help="Specific COM port (omit to auto-connect ALL)")
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate (default: 115200)")
    parser.add_argument("--url", default="http://localhost:5000", help="Web dashboard URL (default: http://localhost:5000)")
    args = parser.parse_args()

    print("═══════════════════════════════════════════════════════════")
    print("  DISASTER SENTINEL — MULTI-NODE 4-PORT USB BRIDGE")
    print("═══════════════════════════════════════════════════════════")
    print(f"  Dashboard: {args.url}")
    print(f"  Baud:      {args.baud}")

    active_threads = {}
    stop_events = {}

    try:
        if args.port:
            print(f"  Mode:      Single Port ({args.port})\n")
            stop_evt = threading.Event()
            listen_port(args.port, args.baud, args.url, stop_evt)
        else:
            print("  Mode:      Auto-Detect Multi-Hub (Monitoring all connected nodes)")
            print("  Plug your 4-Port USB Hub with ESP32s into any USB port.\n")

            while True:
                detected_ports = find_esp32_ports()

                for p, desc in detected_ports:
                    if p not in active_threads or not active_threads[p].is_alive():
                        print(f"  ⚡ Found Node on {p} ({desc})! Starting listener...")
                        stop_evt = threading.Event()
                        t = threading.Thread(
                            target=listen_port,
                            args=(p, args.baud, args.url, stop_evt),
                            daemon=True
                        )
                        t.start()
                        active_threads[p] = t
                        stop_events[p] = stop_evt

                dead = [p for p, t in active_threads.items() if not t.is_alive()]
                for p in dead:
                    del active_threads[p]
                    if p in stop_events:
                        del stop_events[p]

                time.sleep(2.0)

    except KeyboardInterrupt:
        print("\n\nStopping Multi-Node Bridge...")
        for p, evt in stop_events.items():
            evt.set()
        time.sleep(0.5)
        print("Done.")


if __name__ == "__main__":
    main()
