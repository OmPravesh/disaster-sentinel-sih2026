import os
import sys
import joblib
import pandas as pd

# Ensure UTF-8 output encoding for Windows PowerShell / CMD
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, BASE_DIR)

MODELS_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, "models"))
DATA_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, "data"))

def simulate_esp32_reading():
    print("\n=======================================================")
    print("--- [FIR3 Node] Incoming Fire Sensor Telemetry ---")
    print("=======================================================")
    
    # 1. Load the Fire Model
    try:
        model = joblib.load(os.path.join(MODELS_DIR, "fire_model.joblib"))
        print("[OK] Fire ML Model loaded successfully into memory.")
    except FileNotFoundError:
        print("[ERROR] Could not find fire_model.joblib. Did you run train.py?")
        return

    # 2. Simulate receiving data from the ESP32 FIR3 node
    df = pd.read_csv(os.path.join(DATA_DIR, "fire", "fire.csv"))
    clean_df = df.drop(columns=['Unnamed: 0', 'UTC', 'CNT', 'Fire Alarm'], errors='ignore')
    
    # Row 35000 is a fire scenario
    incoming_sensor_data = clean_df.iloc[[35000]] 
    
    print("\n[TELEMETRY] Incoming Live Data from FIR3 Node Sensors:")
    print(incoming_sensor_data.to_string(index=False))

    # 3. Prediction
    print("\n[INFERENCE] Jetson AI Analysis in progress...")
    prediction = model.predict(incoming_sensor_data)

    # 4. Trigger Actuators
    print("=" * 55)
    if prediction[0] == 1:
        print("[CRITICAL ALERT] FIRE DETECTED!")
        print("Jetson Action: GPIO18 Buzzer ON | GPIO23 Strobe ON | Trigger Sprinklers")
    else:
        print("[SAFE] Normal environment conditions.")
        print("Jetson Action: No action required.")
    print("=" * 55)

def simulate_esp32_pollution_reading():
    print("\n=======================================================")
    print("--- [POL4 Node] Incoming Air Quality Telemetry via LoRa ---")
    print("=======================================================")
    
    model_path = os.path.join(MODELS_DIR, "pollution_model.joblib")
    try:
        model = joblib.load(model_path)
        print(f"[OK] Pollution ML Model loaded successfully: {model_path}")
    except FileNotFoundError:
        print(f"[ERROR] {model_path} not found! Run train.py first.")
        return

    # Simulate 3 real-world telemetry packets received over LoRa from POL4
    # (Sensors: MQ-135 on GPIO 34 for gases, GP2Y1010AU0F on GPIO 35 for PM2.5/PM10)
    incoming_lora_packets = [
        {
            "node_id": "POL4",
            "condition": "Clean Fresh Air / Baseline",
            "sensors": {"no2": 14.5, "co": 2.1, "pm10": 42.0, "pm25": 11.5}
        },
        {
            "node_id": "POL4",
            "condition": "Heavy Traffic Congestion / Moderate Spike",
            "sensors": {"no2": 45.0, "co": 7.8, "pm10": 190.0, "pm25": 72.0}
        },
        {
            "node_id": "POL4",
            "condition": "Severe Industrial Smog / Wildfire Hazard",
            "sensors": {"no2": 92.0, "co": 36.5, "pm10": 440.0, "pm25": 255.0}
        }
    ]

    for packet in incoming_lora_packets:
        print(f"\n[PACKET] Received from [{packet['node_id']}] - Scenario: {packet['condition']}")
        input_df = pd.DataFrame([packet["sensors"]])
        print("Telemetry Readings (MQ-135 & GP2Y1010AU0F):")
        print(input_df.to_string(index=False))

        # Run prediction
        alert = model.predict(input_df)[0]

        print("-" * 55)
        if alert == "Hazardous":
            print("[CRITICAL ALERT] HAZARDOUS AIR POLLUTION DETECTED!")
            print("Jetson Action: GPIO18 BUZZER ON | GPIO23 STROBE ON | Trigger SIM800L SMS Alert")
        elif alert == "Warning":
            print("[WARNING] UNHEALTHY AIR POLLUTION DETECTED!")
            print("Jetson Action: Log Warning to Cloud Dashboard | Send Community Advisory")
        else:
            print("[SAFE] AIR QUALITY IS NORMAL.")
            print("Jetson Action: Telemetry logged to database. All actuators idle.")
        print("-" * 55)

def simulate_esp32_flood_reading():
    print("\n=======================================================")
    print("--- [FLD1 Node] Incoming Flood Telemetry via LoRa ---")
    print("=======================================================")
    
    model_path = os.path.join(MODELS_DIR, "flood_model.joblib")
    try:
        model = joblib.load(model_path)
        print(f"[OK] Flood ML Model loaded successfully: {model_path}")
    except FileNotFoundError:
        print(f"[ERROR] {model_path} not found! Run train.py first.")
        return

    # Simulate realistic LoRa packets from Node FLD1:
    # Sensors:
    # 1. HC-SR04 Ultrasonic (River_Water_Level_m)
    # 2. YL-83 Rain Sensor (Rainfall_mm, Rainfall_Intensity_mm_hr)
    # 3. BME280 (Atmospheric_Pressure_hPa, Temperature_C, Relative_Humidity_pct)
    incoming_lora_packets = [
        {
            "node_id": "FLD1",
            "scenario": "Clear / Normal River Stream (Dry Season)",
            "sensors": {
                "River_Water_Level_m": 2.06,
                "Rainfall_mm": 12.24,
                "Rainfall_Intensity_mm_hr": 1.54,
                "Atmospheric_Pressure_hPa": 1005.40,
                "Temperature_C": 33.13,
                "Relative_Humidity_pct": 82.31
            }
        },
        {
            "node_id": "FLD1",
            "scenario": "Heavy Monsoon Shower / River Level Rising",
            "sensors": {
                "River_Water_Level_m": 10.30,
                "Rainfall_mm": 153.33,
                "Rainfall_Intensity_mm_hr": 23.96,
                "Atmospheric_Pressure_hPa": 999.54,
                "Temperature_C": 20.13,
                "Relative_Humidity_pct": 49.31
            }
        },
        {
            "node_id": "FLD1",
            "scenario": "Cyclonic Cloudburst / Critical River Overflow",
            "sensors": {
                "River_Water_Level_m": 12.89,
                "Rainfall_mm": 263.40,
                "Rainfall_Intensity_mm_hr": 49.28,
                "Atmospheric_Pressure_hPa": 981.88,
                "Temperature_C": 17.42,
                "Relative_Humidity_pct": 64.20
            }
        }
    ]

    for packet in incoming_lora_packets:
        print(f"\n[PACKET] Received from [{packet['node_id']}] - Scenario: {packet['scenario']}")
        input_df = pd.DataFrame([packet["sensors"]])
        print("Telemetry Readings (HC-SR04 Ultrasonic + YL-83 Rain + BME280):")
        print(input_df.to_string(index=False))

        # Run prediction on Jetson Hub
        alert = model.predict(input_df)[0]

        print("-" * 55)
        if alert == "Hazardous":
            print("[CRITICAL ALERT] CATASTROPHIC FLOOD / FLASH FLOOD DETECTED!")
            print("Jetson Action: GPIO18 SIREN CONTINUOUS | GPIO23 FLOODLIGHT STROBE | Dispatch SIM800L Emergency SOS to NDRF")
        elif alert == "Warning":
            print("[WARNING] ELEVATED WATER LEVEL & HIGH RAINFALL DETECTED!")
            print("Jetson Action: Alert Dam Authorities | Pre-warn downstream villages via Dashboard")
        else:
            print("[SAFE] WATER LEVEL NORMAL & LOW RAINFALL.")
            print("Jetson Action: Telemetry logged to database. Sluice gates normal.")
        print("-" * 55)

def simulate_esp32_landslide_reading():
    print("\n=======================================================")
    print("--- [SLD2 Node] Incoming Landslide Telemetry via LoRa ---")
    print("=======================================================")
    
    model_path = os.path.join(MODELS_DIR, "landslide_model.joblib")
    try:
        model = joblib.load(model_path)
        print(f"[OK] Landslide ML Model loaded successfully: {model_path}")
    except FileNotFoundError:
        print(f"[ERROR] {model_path} not found! Run train.py first.")
        return

    # Simulate realistic LoRa packets from Node SLD2:
    # Sensors:
    # 1. MPU6050 Gyro/Tilt on GPIO 21/22 (Slope_Angle in degrees)
    # 2. Soil Moisture Sensor v1.2 on GPIO 32 (Soil_Saturation fraction 0-1)
    # 3. BME280 on GPIO 21/22 (Rainfall_mm, Temperature_C, Humidity_percent)
    incoming_lora_packets = [
        {
            "node_id": "SLD2",
            "scenario": "Dry Valley Slope / Stable Bedrock",
            "sensors": {
                "Slope_Angle": 12.0,
                "Soil_Saturation": 0.15,
                "Rainfall_mm": 10.0,
                "Temperature_C": 22.0,
                "Humidity_percent": 45.0
            }
        },
        {
            "node_id": "SLD2",
            "scenario": "Persistent Rain / Soil Saturation Rising",
            "sensors": {
                "Slope_Angle": 32.0,
                "Soil_Saturation": 0.45,
                "Rainfall_mm": 55.0,
                "Temperature_C": 18.0,
                "Humidity_percent": 75.0
            }
        },
        {
            "node_id": "SLD2",
            "scenario": "Steep Mountain Slope Failure / Critical Mudslide",
            "sensors": {
                "Slope_Angle": 58.0,
                "Soil_Saturation": 0.82,
                "Rainfall_mm": 165.0,
                "Temperature_C": 14.0,
                "Humidity_percent": 92.0
            }
        }
    ]

    for packet in incoming_lora_packets:
        print(f"\n[PACKET] Received from [{packet['node_id']}] - Scenario: {packet['scenario']}")
        input_df = pd.DataFrame([packet["sensors"]])
        print("Telemetry Readings (MPU6050 Tilt + Soil Moisture v1.2 + BME280):")
        print(input_df.to_string(index=False))

        # Calculate prediction & risk probability
        prob_hazardous = model.predict_proba(input_df)[0][list(model.classes_).index('Hazardous')]

        print("-" * 55)
        print(f"🧠 Landslide Risk Probability: {prob_hazardous * 100:.1f}%")
        
        if prob_hazardous >= 0.70:
            print("[CRITICAL ALERT] LANDSLIDE IMMINENT / GROUND COLLAPSE DETECTED!")
            print("Jetson Action: GPIO18 SIREN CONTINUOUS | GPIO23 STROBE ON | Trigger SIM800L SOS to NDRF & Hill Evacuation Teams")
        elif prob_hazardous >= 0.35:
            print("[WARNING] SLOPE INSTABILITY & ELEVATED SOIL SATURATION!")
            print("Jetson Action: Restrict Hill Road Traffic | Pre-warn Mountain Communities on Dashboard")
        else:
            print("[SAFE] SLOPE STABLE. NORMAL GROUND CONDITIONS.")
            print("Jetson Action: Telemetry logged to database. Slope angle within safety limits.")
        print("-" * 55)

if __name__ == "__main__":
    simulate_esp32_reading()           # FIR3 Node (Fire)
    simulate_esp32_pollution_reading() # POL4 Node (Air Quality)
    simulate_esp32_flood_reading()     # FLD1 Node (Flood)
    simulate_esp32_landslide_reading() # SLD2 Node (Landslide)