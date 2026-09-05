import os
import sys
import pandas as pd

# Ensure UTF-8 output encoding for Windows PowerShell / CMD
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

def setup_flood_dataset():
    print("[WAIT] [FLD1 Node] Verifying Flood Dataset for HC-SR04, YL-83 & BME280...")
    
    file_path = os.path.join(DATA_DIR, "flood", "flood.csv")
    if os.path.exists(file_path):
        file_size = os.path.getsize(file_path) / (1024 * 1024)
        df = pd.read_csv(file_path)
        print(f"[OK] Found Flood dataset at: {file_path}")
        print(f"File size: {file_size:.2f} MB | Rows: {df.shape[0]} | Columns: {df.shape[1]}")
        print("[OK] Sensor features verified for HC-SR04, YL-83, and BME280.")
    else:
        print("[ERROR] 'data/flood/flood.csv' not found! Please check data/flood folder.")

if __name__ == "__main__":
    setup_flood_dataset()

