import os
import sys
import pandas as pd
from sklearn.model_selection import train_test_split

# Ensure UTF-8 output encoding for Windows PowerShell / CMD
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

def load_and_preprocess_fire_data():
    print("[INFO] Loading the REAL IoT Fire dataset...")
    file_path = os.path.join(DATA_DIR, "fire", "fire.csv")
    
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print("[ERROR] fire.csv not found! Run download_real_data.py first.")
        return None
        
    print(f"Original dataset size: {df.shape[0]} rows and {df.shape[1]} columns")

    # 1. Clean the real data
    # Drop timestamp and index columns
    columns_to_drop = ['Unnamed: 0', 'UTC', 'CNT']
    for col in columns_to_drop:
        if col in df.columns:
            df = df.drop(columns=[col])
            
    print("Dropped unnecessary timestamp columns.")

    # 2. Separate Features (X) and Target (y)
    target_column = 'Fire Alarm'
    
    if target_column in df.columns:
        X = df.drop(columns=[target_column])  
        y = df[target_column]                 
    else:
        print(f"[ERROR] Could not find '{target_column}'.")
        return None

    # 3. Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("\n[OK] --- Fire Data Splitting Complete ---")
    print(f"Training data size: {X_train.shape[0]} rows")
    print(f"Testing data size: {X_test.shape[0]} rows")
    
    return X_train, X_test, y_train, y_test

def load_and_preprocess_pollution_data():
    """
    POL4 Node Preprocessing (MQ-135 Gas Sensor + GP2Y1010AU0F Optical Dust Sensor):
    - Inputs: MQ-135 (no2, co) + Dust Sensor (pm10, pm25)
    - Output: 3-tier disaster alert (Safe, Warning, Hazardous)
    """
    print("\n--- [Node POL4] Loading & Preprocessing Air Quality Data ---")
    
    file_path = os.path.join(DATA_DIR, "pollution", "pollution.csv")
    if not os.path.exists(file_path):
        file_path = os.path.join(DATA_DIR, "pollution", "train.csv")
        
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print("[ERROR] Pollution dataset not found! Run download_pollution_data.py first.")
        return None
        
    print(f"Loaded {df.shape[0]} rows from {file_path}")

    # 1. Map detailed remarks to 3 actionable disaster alert tiers:
    # Safe: Good, Moderate
    # Warning: Unhealthy for Sensitive Groups, Unhealthy
    # Hazardous: Very Unhealthy, Hazardous
    def map_pollution_remark(remark):
        if pd.isna(remark):
            return "Safe"
        remark = str(remark).strip()
        if remark in ["Good", "Moderate"]:
            return "Safe"
        elif "Unhealthy" in remark and "Very" not in remark:
            return "Warning"
        elif "Very Unhealthy" in remark or "Hazardous" in remark:
            return "Hazardous"
        return "Safe"

    df['disaster_status'] = df['Remarks'].apply(map_pollution_remark)

    # 2. Select the hardware-aligned sensor features:
    features = ['no2', 'co', 'pm10', 'pm25']
    target = 'disaster_status'

    df_clean = df[features + [target]].dropna()
    print(f"Cleaned dataset (after removing NaNs): {df_clean.shape[0]} rows")
    print(f"Alert Tier Distribution:\n{df_clean[target].value_counts()}")

    # 3. Train/Test Split (80% training, 20% testing)
    X = df_clean[features]
    y = df_clean[target]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("[OK] --- POL4 Preprocessing & Splitting Complete ---")
    print(f"Training set: {X_train.shape[0]} samples | Testing set: {X_test.shape[0]} samples")

    return X_train, X_test, y_train, y_test

def load_and_preprocess_flood_data():
    """
    FLD1 Node Preprocessing (3-Layer Flood Early Warning):
    - Layer 1 (Primary): Ultrasonic Water Level Sensor ('River_Water_Level_m', 'Rate_of_Rise_m_hr')
    - Layer 2 (Corroborating): YL-83 Rain Sensor ('Rainfall_mm', 'Rainfall_Intensity_mm_hr')
    - Layer 3 (Context): BME280 Environment Sensor ('Atmospheric_Pressure_hPa', 'Temperature_C', 'Relative_Humidity_pct')
    - Target: 'Flood_Extreme_Level' mapped to Safe, Warning, Hazardous
    """
    print("\n--- [Node FLD1] Loading & Preprocessing Flood Sensor Data ---")
    
    file_path = os.path.join(DATA_DIR, "flood", "flood.csv")
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print("[ERROR] Flood dataset not found! Run download_flood_data.py first.")
        return None
        
    print(f"Loaded {df.shape[0]} rows from {file_path}")

    # 1. Map target flood levels to 3 SIH Alert Tiers
    level_map = {0: "Safe", 1: "Warning", 2: "Hazardous"}
    if 'Flood_Extreme_Level' in df.columns:
        df['disaster_status'] = df['Flood_Extreme_Level'].map(level_map).fillna("Safe")
    elif 'Flood' in df.columns:
        df['disaster_status'] = df['Flood'].map({0: "Safe", 1: "Hazardous"}).fillna("Safe")

    # 2. Select 3-layer sensor telemetry features
    features = [
        'River_Water_Level_m', 'Rate_of_Rise_m_hr', 
        'Rainfall_mm', 'Rainfall_Intensity_mm_hr', 
        'Atmospheric_Pressure_hPa', 'Temperature_C', 'Relative_Humidity_pct'
    ]
    target = 'disaster_status'

    df_clean = df[features + [target]].dropna()
    print(f"Cleaned flood dataset size: {df_clean.shape[0]} samples")
    print(f"Alert Tier Breakdown:\n{df_clean[target].value_counts()}")

    # 3. Train/Test Split
    X = df_clean[features]
    y = df_clean[target]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"[OK] --- FLD1 Preprocessing Complete ({X_train.shape[0]} train / {X_test.shape[0]} test) ---")
    return X_train, X_test, y_train, y_test

def load_and_preprocess_landslide_data():
    """
    SLD2 Node Preprocessing (3-Layer Landslide Warning):
    - Layer 1 (Primary): MPU6050 Accelerometer/Tilt ('Slope_Angle', 'Vibration_Intensity')
    - Layer 2 (Corroborating): Soil Moisture Sensor v1.2 ('Soil_Saturation')
    - Layer 3 (Context): BME280 Environment Sensor ('Rainfall_mm', 'Temperature_C', 'Humidity_percent')
    - Target: 'Label' mapped to Safe (0) and Hazardous (1)
    """
    print("\n--- [Node SLD2] Loading & Preprocessing Landslide Sensor Data ---")
    
    file_path = os.path.join(DATA_DIR, "landslide", "landslide.csv")
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print("[ERROR] Landslide dataset not found! Run download_landslide_data.py first.")
        return None
        
    print(f"Loaded {df.shape[0]} rows from {file_path}")

    # 1. Map target label (0: Safe, 1: Hazardous)
    df['Alert_Level'] = df['Label'].map({0: 'Safe', 1: 'Hazardous'})

    # 2. Select physical IoT features corresponding to SLD2 sensors
    iot_features = [
        'Slope_Angle', 
        'Soil_Saturation', 
        'Rainfall_mm', 
        'Temperature_C', 
        'Humidity_percent'
    ]
    
    X = df[iot_features]
    y = df['Alert_Level']

    # 3. Train-Test Split (80% train, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("[OK] Preprocessing complete for SLD2 Node.")
    print(f"Sensor Features: {iot_features}")
    print(f"Train samples: {X_train.shape[0]} | Test samples: {X_test.shape[0]}")
    
    return X_train, X_test, y_train, y_test

if __name__ == "__main__":
    result_fire = load_and_preprocess_fire_data()
    result_pollution = load_and_preprocess_pollution_data()
    result_flood = load_and_preprocess_flood_data()
    result_landslide = load_and_preprocess_landslide_data()