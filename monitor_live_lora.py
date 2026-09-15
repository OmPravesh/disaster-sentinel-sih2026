import os
import sys
import time
from datetime import datetime

# Ensure unbuffered UTF-8 output on Windows & Linux
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

def print_flush(text, color_code=None):
    if color_code and sys.platform != "win32":
        print(f"{color_code}{text}\033[0m", flush=True)
    else:
        print(text, flush=True)

# -------------------------------------------------------------
# HUMAN-READABLE LORA PACKET STREAM MONITOR
# -------------------------------------------------------------

def monitor_jetson_rx_log():
    """Reads live over-the-air LoRa packets received on Jetson SX1278 SPI."""
    print_flush("=" * 80)
    print_flush("  🛡️  DISASTER SENTINEL — REAL-TIME LORA RECEIVER MONITOR")
    print_flush("  NVIDIA Jetson Orin Nano Gateway · 433MHz SX1278 SPI Link")
    print_flush("=" * 80)

    log_path = "/tmp/sentinel_main.log"
    if not os.path.exists(log_path):
        print_flush(f"⚠️ Waiting for log file {log_path}...")

    print_flush("✅ [JETSON LORA RX SPI] Active Receiver Feed:\n")

    packet_count = 0

    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            # Read recent historical log lines first so screen is never blank
            lines = f.readlines()
            recent_lines = lines[-15:] if len(lines) >= 15 else lines
            for line in recent_lines:
                text = line.strip()
                if "receiver.lora_receiver" in text and ("NORMAL" in text or "PRIORITY" in text or "SLD2" in text):
                    packet_count += 1
                    print_flush(f"📡 {text}")

            print_flush("\n─── 📡 WAITING FOR NEXT OVER-THE-AIR LORA PACKET (~5s) ───\n", "\033[93m")

            # Tail new live lines continuously
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.05)
                    continue

                text = line.strip()
                if "receiver.lora_receiver" in text and ("NORMAL" in text or "PRIORITY" in text or "SLD2" in text):
                    packet_count += 1
                    now = datetime.now().strftime("%H:%M:%S")

                    print_flush("─" * 80)
                    print_flush(f"🎉 PACKET #{packet_count} RECEIVED OVER 433MHz LORA | TIME: {now}", "\033[92m")
                    print_flush(f"   {text}")
                    print_flush("─" * 80 + "\n")

                elif "ERROR" in text or "Processing error" in text:
                    print_flush(f"⚠️ [JETSON ERROR]: {text}", "\033[91m")

    except KeyboardInterrupt:
        print_flush("\nStopped live monitor.")
    except Exception as e:
        print_flush(f"Monitor error: {e}")

if __name__ == "__main__":
    monitor_jetson_rx_log()
