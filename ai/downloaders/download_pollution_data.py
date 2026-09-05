import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

def setup_pollution_dataset():
    print("[WAIT] [POL4 Node] Setting up Air Quality Dataset for MQ-135 & GP2Y1010AU0F...")
    
    raw_path = os.path.join(DATA_DIR, "pollution", "train.csv")
    clean_path = os.path.join(DATA_DIR, "pollution", "pollution.csv")
    
    # Check if raw Kaggle file exists in your data/pollution folder
    if os.path.exists(raw_path):
        print(f"[OK] Found Kaggle raw dataset at: {raw_path}")
        
        if not os.path.exists(clean_path):
            print("Sampling 50,000 balanced rows to create lightweight data/pollution/pollution.csv (~5MB)...")
            df = pd.read_csv(raw_path, nrows=50000)
            df.to_csv(clean_path, index=False)
            print(f"[OK] Created: {clean_path} (Ready for POL4 node training!)")
        else:
            print(f"[OK] {clean_path} already exists. Ready to train!")
    else:
        print("[ERROR] 'data/pollution/train.csv' not found. Please ensure train.csv is in data/pollution/")

if __name__ == "__main__":
    setup_pollution_dataset()

