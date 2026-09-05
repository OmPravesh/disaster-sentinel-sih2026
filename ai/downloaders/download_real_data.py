import urllib.request
import os

print("⏳ Downloading the REAL 60,000-row IoT Smoke Detection Dataset...")
print("Please wait, this might take a few seconds (it is about 5MB).")

# Direct URL to a GitHub mirror of the Kaggle IoT Smoke Detection dataset
url = "https://raw.githubusercontent.com/joshgivens/DRE-NP-MissingData/main/real_world_data/smoke_detection_iot.csv"

# Where to save it
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
save_path = os.path.join(DATA_DIR, "fire", "fire.csv")
os.makedirs(os.path.dirname(save_path), exist_ok=True)

try:
    # Download the file
    urllib.request.urlretrieve(url, save_path)
    
    # Check the file size
    file_size = os.path.getsize(save_path) / (1024 * 1024) # Convert to MB
    print(f"✅ Success! Real dataset downloaded and saved to: {save_path}")
    print(f"File size: {file_size:.2f} MB")
    
except Exception as e:
    print(f"❌ Error downloading file: {e}")