"""
Disaster Sentinel — Windows Laptop Live Terminal Monitor
=========================================================
Streams real-time LoRa telemetry from the NVIDIA Jetson Orin Nano
over Wi-Fi directly to your Windows PowerShell terminal.

Usage:
    python tools/live_monitor.py
    python tools/live_monitor.py --ip 192.168.1.50
"""

import sys
import time
import json
import argparse
import urllib.request
from datetime import datetime

# Windows terminal ANSI escape color support
if sys.platform == "win32":
    try:
        import os
        os.system("")
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Terminal colors
CLR_RESET   = "\033[0m"
CLR_BOLD    = "\033[1m"
CLR_DIM     = "\033[2m"
CLR_RED     = "\033[91m"
CLR_GREEN   = "\033[92m"
CLR_YELLOW  = "\033[93m"
CLR_BLUE    = "\033[94m"
CLR_MAGENTA = "\033[95m"
CLR_CYAN    = "\033[96m"
CLR_WHITE   = "\033[97m"
CLR_BG_DARK = "\033[48;5;234m"

def format_node_status(node):
    connected = node.get("connected", False)
    last_ago = node.get("last_seen_ago")
    status_str = node.get("status", "Safe")

    if not connected:
        if last_ago is not None:
            return f"{CLR_RED}{CLR_DIM}⚪ DISCONNECTED (offline {last_ago:.0f}s ago){CLR_RESET}"
        return f"{CLR_RED}{CLR_DIM}⚪ DISCONNECTED (no data received){CLR_RESET}"

    # Connected and active
    ago_str = f"{last_ago:.0f}s ago" if last_ago is not None else "live"
    status_lower = str(status_str).lower()
    if "hazard" in status_lower or "critical" in status_lower:
        badge = f"{CLR_RED}{CLR_BOLD}🚨 {status_str.upper()}{CLR_RESET}"
    elif "warn" in status_lower or "elevated" in status_lower:
        badge = f"{CLR_YELLOW}{CLR_BOLD}⚠️  {status_str.upper()}{CLR_RESET}"
    else:
        badge = f"{CLR_GREEN}{CLR_BOLD}✅ {status_str.upper()}{CLR_RESET}"
    
    return f"{badge} {CLR_CYAN}[ACTIVE · {ago_str}]{CLR_RESET}"

def run_monitor(jetson_ip: str = "192.168.1.50", port: int = 5000, interval: float = 2.0):
    url = f"http://{jetson_ip}:{port}/api/nodes"
    
    print("\n" + "=" * 78)
    print(f"{CLR_CYAN}{CLR_BOLD}  🛡️  DISASTER SENTINEL — LIVE WI-FI TERMINAL MONITOR{CLR_RESET}")
    print(f"  Streaming live telemetry from Jetson Orin Nano at: {CLR_WHITE}{url}{CLR_RESET}")
    print("  Press Ctrl+C to stop.")
    print("=" * 78 + "\n")

    seq_count = 0

    while True:
        seq_count += 1
        now_str = datetime.now().strftime("%H:%M:%S")

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "DisasterSentinel-Monitor/1.0"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            hub = data.get("hub", {})
            nodes = data.get("nodes", {})
            pol4 = nodes.get("POL4", {})
            fld1 = nodes.get("FLD1", {})
            sld2 = nodes.get("SLD2", {})
            fir3 = nodes.get("FIR3", {})

            # Terminal Header Card
            print(f"{CLR_BG_DARK}{CLR_WHITE} [SYNC #{seq_count:04d} | {now_str}]  Hub: {hub.get('hub_id', 'JETSON')}  |  LoRa: {CLR_GREEN}SX1278 433MHz (ONLINE){CLR_WHITE}  |  Alerts: {hub.get('active_alerts_count', 0)} {CLR_RESET}")

            # 1. POL4 Card (Pollution)
            p_sens = pol4.get("sensors", {})
            p_pm25 = p_sens.get("pm25", 0.0)
            p_pm10 = p_sens.get("pm10", 0.0)
            p_co   = p_sens.get("co", 0.0)
            p_rssi = pol4.get("lora_rssi", -70)
            p_stat = format_node_status(pol4)
            if pol4.get("connected"):
                print(f"  {CLR_CYAN}{CLR_BOLD}🍃 POL4 (Air Basin){CLR_RESET}   AQI/CO: {CLR_BOLD}{p_co:.1f} ppm{CLR_RESET} | PM2.5: {CLR_BOLD}{p_pm25:.1f} µg/m³{CLR_RESET} (PM10: {p_pm10:.1f}) | RSSI: {p_rssi} dBm | {p_stat}")
            else:
                print(f"  {CLR_DIM}🍃 POL4 (Air Basin)   Last PM2.5: {p_pm25:.1f} µg/m³ | {p_stat}{CLR_RESET}")

            # 2. FLD1 Card (Flood)
            fl_sens = fld1.get("sensors", {})
            fl_w = fl_sens.get("River_Water_Level_m", 0.0)
            fl_r = fl_sens.get("Rainfall_Intensity_mm_hr", 0.0)
            fl_stat = format_node_status(fld1)
            if fld1.get("connected"):
                print(f"  {CLR_BLUE}{CLR_BOLD}🌊 FLD1 (Flood Catch){CLR_RESET} Water: {CLR_BOLD}{fl_w:.2f} m{CLR_RESET}    | Rain: {CLR_BOLD}{fl_r:.2f} mm/h{CLR_RESET}        | RSSI: {fld1.get('lora_rssi', -68)} dBm | {fl_stat}")
            else:
                print(f"  {CLR_DIM}🌊 FLD1 (Flood Catch) Last Water: {fl_w:.2f} m | {fl_stat}{CLR_RESET}")

            # 3. SLD2 Card (Landslide)
            sl_sens = sld2.get("sensors", {})
            sl_ang = sl_sens.get("Slope_Angle", 0.0)
            sl_sat = sl_sens.get("Soil_Saturation", 0.0) * 100
            sl_stat = format_node_status(sld2)
            if sld2.get("connected"):
                print(f"  {CLR_MAGENTA}{CLR_BOLD}⛰️  SLD2 (Landslide){CLR_RESET}   Tilt: {CLR_BOLD}{sl_ang:.1f}°{CLR_RESET}       | Soil: {CLR_BOLD}{sl_sat:.1f}%{CLR_RESET}              | RSSI: {sld2.get('lora_rssi', -72)} dBm | {sl_stat}")
            else:
                print(f"  {CLR_DIM}⛰️  SLD2 (Landslide)   Last Tilt: {sl_ang:.1f}° | {sl_stat}{CLR_RESET}")

            # 4. FIR3 Card (Fire)
            fi_sens = fir3.get("sensors", {})
            fi_gas = fi_sens.get("TVOC[ppb]", 0.0)
            fi_tmp = fi_sens.get("Temperature[C]", 0.0)
            fi_stat = format_node_status(fir3)
            if fir3.get("connected"):
                print(f"  {CLR_YELLOW}{CLR_BOLD}🔥 FIR3 (Forest Fire){CLR_RESET} Gas: {CLR_BOLD}{fi_gas:.0f} ppb{CLR_RESET}    | Temp: {CLR_BOLD}{fi_tmp:.1f} °C{CLR_RESET}            | RSSI: {fir3.get('lora_rssi', -65)} dBm | {fi_stat}")
            else:
                print(f"  {CLR_DIM}🔥 FIR3 (Forest Fire) Last Gas: {fi_gas:.0f} ppb | {fi_stat}{CLR_RESET}")

            print(f"{CLR_DIM}  " + "─" * 74 + f"{CLR_RESET}")

        except urllib.error.URLError as e:
            print(f"  {CLR_RED}⚠️ Connection to Jetson at {jetson_ip} failed ({e.reason}). Retrying in {interval}s...{CLR_RESET}")
        except Exception as e:
            print(f"  {CLR_RED}⚠️ Error: {e}{CLR_RESET}")

        time.sleep(interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Disaster Sentinel - Laptop Live Terminal Stream")
    parser.add_argument("--ip", default="192.168.1.50", help="IP address of NVIDIA Jetson Orin Nano")
    parser.add_argument("--port", type=int, default=5000, help="Web dashboard port")
    parser.add_argument("--interval", type=float, default=2.5, help="Poll interval in seconds")
    args = parser.parse_args()

    try:
        run_monitor(args.ip, args.port, args.interval)
    except KeyboardInterrupt:
        print("\n\nStopped live monitor. Have a great demo!\n")

