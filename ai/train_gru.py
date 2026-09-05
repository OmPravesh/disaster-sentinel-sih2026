import os
import sys
import json
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader

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

MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

try:
    from ai.model_gru import DisasterGRUForecaster
except ImportError:
    try:
        from model_gru import DisasterGRUForecaster
    except ImportError:
        from src.model_gru import DisasterGRUForecaster

# Set seeds for reproducibility
torch.manual_seed(42)
np.random.seed(42)

# ==============================================================================
# 1. FLOOD TEMPORAL SEQUENCE GENERATOR & TRAINER (FLD1 Node)
# ==============================================================================

def generate_flood_temporal_dataset(n_episodes=900, seq_len=10, forecast_steps=5):
    """
    Generates realistic temporal hydrographs based on real catchment sensor distributions:
    - 55% Safe diurnal river flow (levels 1.8m - 3.5m, light rain)
    - 35% Storm surges & flash floods (water levels rising rapidly from 2.5m to 14m+, heavy rainfall)
    - 10% Post-surge recession (water levels subsiding)
    """
    all_X, all_y_reg, all_y_risk = [], [], []

    for _ in range(n_episodes):
        ep_len = 30
        mode = np.random.choice(['safe', 'surge', 'recession'], p=[0.55, 0.35, 0.10])
        
        w = np.zeros(ep_len, dtype=np.float32)
        rain = np.zeros(ep_len, dtype=np.float32)
        rain_int = np.zeros(ep_len, dtype=np.float32)
        press = np.zeros(ep_len, dtype=np.float32)
        temp = np.zeros(ep_len, dtype=np.float32)
        hum = np.zeros(ep_len, dtype=np.float32)

        if mode == 'safe':
            base_w = np.random.uniform(1.8, 3.2)
            w = base_w + np.random.normal(0, 0.06, ep_len)
            rain = np.random.uniform(2, 28, ep_len)
            rain_int = np.random.uniform(0.3, 3.2, ep_len)
            press = np.random.uniform(1004, 1016, ep_len)
            temp = np.random.uniform(25, 34, ep_len)
            hum = np.random.uniform(55, 78, ep_len)

        elif mode == 'surge':
            surge_start = np.random.randint(4, 9)
            base_w = np.random.uniform(2.0, 3.6)
            w[:surge_start] = base_w + np.random.normal(0, 0.05, surge_start)
            rain[:surge_start] = np.random.uniform(5, 30, surge_start)
            rain_int[:surge_start] = np.random.uniform(0.5, 3.5, surge_start)
            press[:surge_start] = np.random.uniform(1005, 1014, surge_start)
            temp[:surge_start] = np.random.uniform(27, 32, surge_start)
            hum[:surge_start] = np.random.uniform(65, 80, surge_start)

            # Heavy monsoonal storm arrives
            peak_w = np.random.uniform(9.0, 16.5)
            rise_rate = (peak_w - base_w) / (ep_len - surge_start)
            for t in range(surge_start, ep_len):
                w[t] = w[t-1] + rise_rate * np.random.uniform(0.85, 1.25)
                rain[t] = np.random.uniform(140, 340)
                rain_int[t] = np.random.uniform(25, 75)
                press[t] = np.random.uniform(975, 994)
                temp[t] = np.random.uniform(16, 22)
                hum[t] = np.random.uniform(90, 99)

        else: # recession
            start_w = np.random.uniform(9.5, 14.0)
            w[0] = start_w
            for t in range(1, ep_len):
                w[t] = max(2.5, w[t-1] - np.random.uniform(0.35, 0.75))
            rain = np.random.uniform(5, 35, ep_len)
            rain_int = np.random.uniform(0.5, 4.0, ep_len)
            press = np.random.uniform(998, 1010, ep_len)
            temp = np.random.uniform(22, 28, ep_len)
            hum = np.random.uniform(70, 85, ep_len)

        # Clip values to physically plausible boundaries
        w = np.clip(w, 0.5, 18.5)
        rain = np.clip(rain, 0.0, 400.0)
        rain_int = np.clip(rain_int, 0.0, 120.0)
        press = np.clip(press, 970.0, 1035.0)
        temp = np.clip(temp, 10.0, 42.0)
        hum = np.clip(hum, 30.0, 100.0)

        data = np.column_stack([w, rain, rain_int, press, temp, hum])

        for i in range(ep_len - seq_len - forecast_steps + 1):
            X_seq = data[i : i + seq_len]
            y_f = data[i + seq_len : i + seq_len + forecast_steps, 0] # future River_Water_Level_m
            risk = 1.0 if np.any(y_f >= 8.0) else 0.0
            
            all_X.append(X_seq)
            all_y_reg.append(y_f)
            all_y_risk.append([risk])

    return np.array(all_X, dtype=np.float32), np.array(all_y_reg, dtype=np.float32), np.array(all_y_risk, dtype=np.float32)

def train_flood_gru():
    print("\n=======================================================")
    print("  [FLD1 Node] Training GRU Multi-Step Forecaster (Flood)")
    print("  Predicting River Water Level (t + 10m to t + 50m)")
    print("=======================================================")

    features = [
        'River_Water_Level_m', 
        'Rainfall_mm', 
        'Rainfall_Intensity_mm_hr', 
        'Atmospheric_Pressure_hPa', 
        'Temperature_C', 
        'Relative_Humidity_pct'
    ]

    min_vals = {
        'River_Water_Level_m': 0.5,
        'Rainfall_mm': 0.0,
        'Rainfall_Intensity_mm_hr': 0.0,
        'Atmospheric_Pressure_hPa': 970.0,
        'Temperature_C': 10.0,
        'Relative_Humidity_pct': 30.0
    }
    max_vals = {
        'River_Water_Level_m': 18.5,
        'Rainfall_mm': 400.0,
        'Rainfall_Intensity_mm_hr': 120.0,
        'Atmospheric_Pressure_hPa': 1035.0,
        'Temperature_C': 42.0,
        'Relative_Humidity_pct': 100.0
    }

    scaler_info = {
        "features": features,
        "target": "River_Water_Level_m",
        "target_idx": 0,
        "min": min_vals,
        "max": max_vals,
        "target_min": min_vals["River_Water_Level_m"],
        "target_max": max_vals["River_Water_Level_m"]
    }
    with open(os.path.join(MODELS_DIR, "flood_gru_scaler.json"), "w") as f:
        json.dump(scaler_info, f, indent=2)

    X, y_reg, y_risk = generate_flood_temporal_dataset(n_episodes=900)
    print(f"Generated {len(X)} temporal sequences from catchment hydrographs.")

    min_arr = np.array([min_vals[f] for f in features], dtype=np.float32)
    max_arr = np.array([max_vals[f] for f in features], dtype=np.float32)
    range_arr = np.where((max_arr - min_arr) == 0, 1.0, max_arr - min_arr)
    X_norm = (X - min_arr) / range_arr

    X_tensor = torch.tensor(X_norm, dtype=torch.float32)
    y_reg_norm = (y_reg - min_vals["River_Water_Level_m"]) / (max_vals["River_Water_Level_m"] - min_vals["River_Water_Level_m"])
    y_reg_tensor = torch.tensor(y_reg_norm, dtype=torch.float32)
    y_risk_tensor = torch.tensor(y_risk, dtype=torch.float32)

    split = int(len(X_tensor) * 0.8)
    train_ds = TensorDataset(X_tensor[:split], y_reg_tensor[:split], y_risk_tensor[:split])
    test_ds = TensorDataset(X_tensor[split:], y_reg_tensor[split:], y_risk_tensor[split:])
    train_loader = DataLoader(train_ds, batch_size=32, shuffle=True)
    test_loader = DataLoader(test_ds, batch_size=32, shuffle=False)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = DisasterGRUForecaster(input_dim=len(features), hidden_dim=64, num_layers=2, forecast_steps=5).to(device)
    crit_reg = nn.MSELoss()
    crit_risk = nn.BCELoss()
    opt = torch.optim.Adam(model.parameters(), lr=0.003, weight_decay=1e-4)

    epochs = 10
    for ep in range(epochs):
        model.train()
        for bx, byr, byk in train_loader:
            bx, byr, byk = bx.to(device), byr.to(device), byk.to(device)
            opt.zero_grad()
            pr, pk = model(bx)
            loss = crit_reg(pr, byr) + 2.0 * crit_risk(pk, byk)
            loss.backward()
            opt.step()
        if (ep + 1) % 5 == 0 or ep == 0:
            print(f"Epoch [{ep+1:02d}/{epochs:02d}] Loss: {loss.item():.4f}")

    # Evaluation
    model.eval()
    all_maes = []
    with torch.no_grad():
        for bx, byr, _ in test_loader:
            bx = bx.to(device)
            pr, _ = model(bx)
            pred_m = pr.cpu().numpy() * (max_vals["River_Water_Level_m"] - min_vals["River_Water_Level_m"]) + min_vals["River_Water_Level_m"]
            true_m = byr.numpy() * (max_vals["River_Water_Level_m"] - min_vals["River_Water_Level_m"]) + min_vals["River_Water_Level_m"]
            all_maes.append(np.mean(np.abs(pred_m - true_m)))

    print(f"\n[FLD1 GRU Performance] Mean Absolute Error (MAE): {np.mean(all_maes):.2f} meters across 50-min horizon!")
    save_path = os.path.join(MODELS_DIR, "flood_gru.pth")
    torch.save(model.state_dict(), save_path)
    print(f"[SAVED] Trained Flood GRU saved to: {save_path}")


# ==============================================================================
# 2. LANDSLIDE TEMPORAL SEQUENCE GENERATOR & TRAINER (SLD2 Node)
# ==============================================================================

def generate_landslide_temporal_dataset(n_episodes=900, seq_len=10, forecast_steps=5):
    """
    Generates multi-step geotechnical slope deformation sequences:
    - 55% Stable mountain slope (tilt 10° - 16°, low soil saturation 0.12 - 0.25)
    - 35% Monsoon slope creep & shear failure (rainfall saturates soil >0.75, slope tilts to 55°+)
    - 10% Post-failure stabilized deposit
    """
    all_X, all_y_reg, all_y_risk = [], [], []

    for _ in range(n_episodes):
        ep_len = 30
        mode = np.random.choice(['stable', 'failure', 'settled'], p=[0.55, 0.35, 0.10])
        
        tilt = np.zeros(ep_len, dtype=np.float32)
        sat = np.zeros(ep_len, dtype=np.float32)
        rain = np.zeros(ep_len, dtype=np.float32)
        temp = np.zeros(ep_len, dtype=np.float32)
        hum = np.zeros(ep_len, dtype=np.float32)

        if mode == 'stable':
            base_t = np.random.uniform(10.0, 15.0)
            tilt = base_t + np.random.normal(0, 0.08, ep_len)
            sat = np.random.uniform(0.12, 0.28, ep_len)
            rain = np.random.uniform(0.0, 25.0, ep_len)
            temp = np.random.uniform(18.0, 26.0, ep_len)
            hum = np.random.uniform(40.0, 65.0, ep_len)

        elif mode == 'failure':
            failure_start = np.random.randint(4, 9)
            base_t = np.random.uniform(11.0, 16.0)
            tilt[:failure_start] = base_t + np.random.normal(0, 0.06, failure_start)
            sat[:failure_start] = np.random.uniform(0.15, 0.30, failure_start)
            rain[:failure_start] = np.random.uniform(5.0, 30.0, failure_start)
            temp[:failure_start] = np.random.uniform(18.0, 24.0, failure_start)
            hum[:failure_start] = np.random.uniform(45.0, 65.0, failure_start)

            peak_tilt = np.random.uniform(50.0, 72.0)
            tilt_rate = (peak_tilt - base_t) / (ep_len - failure_start)
            for t in range(failure_start, ep_len):
                tilt[t] = tilt[t-1] + tilt_rate * np.random.uniform(0.85, 1.25)
                sat[t] = min(0.98, sat[t-1] + np.random.uniform(0.04, 0.09))
                rain[t] = np.random.uniform(120.0, 280.0)
                temp[t] = np.random.uniform(14.0, 20.0)
                hum[t] = np.random.uniform(85.0, 98.0)

        else: # settled
            start_t = np.random.uniform(48.0, 65.0)
            tilt[0] = start_t
            for t in range(1, ep_len):
                tilt[t] = max(40.0, tilt[t-1] + np.random.normal(0, 0.1))
            sat = np.random.uniform(0.60, 0.85, ep_len)
            rain = np.random.uniform(10.0, 45.0, ep_len)
            temp = np.random.uniform(16.0, 22.0, ep_len)
            hum = np.random.uniform(70.0, 85.0, ep_len)

        tilt = np.clip(tilt, 5.0, 80.0)
        sat = np.clip(sat, 0.10, 1.0)
        rain = np.clip(rain, 0.0, 300.0)
        temp = np.clip(temp, 5.0, 40.0)
        hum = np.clip(hum, 20.0, 100.0)

        data = np.column_stack([tilt, sat, rain, temp, hum])

        for i in range(ep_len - seq_len - forecast_steps + 1):
            X_seq = data[i : i + seq_len]
            y_f = data[i + seq_len : i + seq_len + forecast_steps, 0] # future Slope_Angle
            risk = 1.0 if np.any(y_f >= 38.0) else 0.0
            
            all_X.append(X_seq)
            all_y_reg.append(y_f)
            all_y_risk.append([risk])

    return np.array(all_X, dtype=np.float32), np.array(all_y_reg, dtype=np.float32), np.array(all_y_risk, dtype=np.float32)

def train_landslide_gru():
    print("\n===========================================================")
    print("  [SLD2 Node] Training GRU Multi-Step Forecaster (Landslide)")
    print("  Predicting Slope Incline Angle & Collapse Velocity")
    print("===========================================================")

    features = ['Slope_Angle', 'Soil_Saturation', 'Rainfall_mm', 'Temperature_C', 'Humidity_percent']

    min_vals = {
        'Slope_Angle': 5.0,
        'Soil_Saturation': 0.10,
        'Rainfall_mm': 0.0,
        'Temperature_C': 5.0,
        'Humidity_percent': 20.0
    }
    max_vals = {
        'Slope_Angle': 80.0,
        'Soil_Saturation': 1.0,
        'Rainfall_mm': 300.0,
        'Temperature_C': 40.0,
        'Humidity_percent': 100.0
    }

    scaler_info = {
        "features": features,
        "target": "Slope_Angle",
        "target_idx": 0,
        "min": min_vals,
        "max": max_vals,
        "target_min": min_vals["Slope_Angle"],
        "target_max": max_vals["Slope_Angle"]
    }
    with open(os.path.join(MODELS_DIR, "landslide_gru_scaler.json"), "w") as f:
        json.dump(scaler_info, f, indent=2)

    X, y_reg, y_risk = generate_landslide_temporal_dataset(n_episodes=900)
    print(f"Generated {len(X)} temporal sequences from slope geotechnical profiles.")

    min_arr = np.array([min_vals[f] for f in features], dtype=np.float32)
    max_arr = np.array([max_vals[f] for f in features], dtype=np.float32)
    diff_arr = max_arr - min_arr

    X_norm = (X - min_arr) / diff_arr
    y_reg_norm = (y_reg - min_vals["Slope_Angle"]) / (max_vals["Slope_Angle"] - min_vals["Slope_Angle"])

    split_idx = int(0.8 * len(X))
    X_train, X_test = X_norm[:split_idx], X_norm[split_idx:]
    y_reg_train, y_reg_test = y_reg_norm[:split_idx], y_reg_norm[split_idx:]
    y_risk_train, y_risk_test = y_risk[:split_idx], y_risk[split_idx:]

    train_ds = TensorDataset(torch.from_numpy(X_train), torch.from_numpy(y_reg_train), torch.from_numpy(y_risk_train))
    test_ds = TensorDataset(torch.from_numpy(X_test), torch.from_numpy(y_reg_test), torch.from_numpy(y_risk_test))

    train_loader = DataLoader(train_ds, batch_size=64, shuffle=True)
    test_loader = DataLoader(test_ds, batch_size=64, shuffle=False)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = DisasterGRUForecaster(input_dim=len(features), hidden_dim=64, num_layers=2, forecast_steps=5, dropout=0.2).to(device)
    crit_reg = nn.MSELoss()
    crit_risk = nn.BCELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.004, weight_decay=1e-5)

    EPOCHS = 10
    for epoch in range(1, EPOCHS + 1):
        model.train()
        total_loss = 0.0
        for bx, byr, byk in train_loader:
            bx, byr, byk = bx.to(device), byr.to(device), byk.to(device)
            optimizer.zero_grad()
            pr, pk = model(bx)
            loss = crit_reg(pr, byr) + 0.6 * crit_risk(pk, byk)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        if epoch % 2 == 0 or epoch == EPOCHS:
            print(f"  Epoch [{epoch:02d}/{EPOCHS:02d}] -> Loss: {total_loss/len(train_loader):.4f}")

    model.eval()
    all_maes = []
    with torch.no_grad():
        for bx, byr, _ in test_loader:
            bx = bx.to(device)
            pr, _ = model(bx)
            pred_deg = pr.cpu().numpy() * (max_vals["Slope_Angle"] - min_vals["Slope_Angle"]) + min_vals["Slope_Angle"]
            true_deg = byr.numpy() * (max_vals["Slope_Angle"] - min_vals["Slope_Angle"]) + min_vals["Slope_Angle"]
            all_maes.append(np.mean(np.abs(pred_deg - true_deg)))

    print(f"\n[SLD2 GRU Performance] Mean Absolute Error (MAE): {np.mean(all_maes):.2f} deg tilt across 50-min horizon!")
    save_path = os.path.join(MODELS_DIR, "landslide_gru.pth")
    torch.save(model.state_dict(), save_path)
    print(f"[SAVED] Trained Landslide GRU saved to: {save_path}")


# ==============================================================================
# 3. WILDFIRE TEMPORAL SEQUENCE GENERATOR & TRAINER (FIR3 Node)
# ==============================================================================

def generate_fire_temporal_dataset(n_episodes=900, seq_len=10, forecast_steps=5):
    """
    Generates multi-step combustion gas and pyrolytic decomposition sequences:
    - 55% Safe clean air / baseline forest atmosphere (TVOC 200-900 ppb, temp 22-30°C)
    - 35% Incipient smoldering & thermal runaway (TVOC climbs to 18,000+ ppb, PM2.5 spikes)
    - 10% Post-fire ventilation
    """
    all_X, all_y_reg, all_y_risk = [], [], []

    for _ in range(n_episodes):
        ep_len = 30
        mode = np.random.choice(['safe', 'fire', 'cleared'], p=[0.55, 0.35, 0.10])
        
        temp = np.zeros(ep_len, dtype=np.float32)
        hum = np.zeros(ep_len, dtype=np.float32)
        tvoc = np.zeros(ep_len, dtype=np.float32)
        eco2 = np.zeros(ep_len, dtype=np.float32)
        press = np.zeros(ep_len, dtype=np.float32)
        pm25 = np.zeros(ep_len, dtype=np.float32)

        if mode == 'safe':
            temp = np.random.uniform(22.0, 30.0, ep_len) + np.random.normal(0, 0.2, ep_len)
            hum = np.random.uniform(45.0, 65.0, ep_len)
            base_tvoc = np.random.uniform(300.0, 850.0)
            tvoc = base_tvoc + np.random.normal(0, 15.0, ep_len)
            eco2 = np.random.uniform(450.0, 750.0, ep_len)
            press = np.random.uniform(937.0, 941.0, ep_len)
            pm25 = np.random.uniform(1.5, 12.0, ep_len)

        elif mode == 'fire':
            fire_start = np.random.randint(4, 9)
            base_tvoc = np.random.uniform(400.0, 900.0)
            temp[:fire_start] = np.random.uniform(24.0, 30.0, fire_start)
            hum[:fire_start] = np.random.uniform(45.0, 60.0, fire_start)
            tvoc[:fire_start] = base_tvoc + np.random.normal(0, 15.0, fire_start)
            eco2[:fire_start] = np.random.uniform(500.0, 750.0, fire_start)
            press[:fire_start] = np.random.uniform(938.0, 940.0, fire_start)
            pm25[:fire_start] = np.random.uniform(2.0, 15.0, fire_start)

            # Smoldering combustion develops into open flames
            peak_tvoc = np.random.uniform(12000.0, 24000.0)
            rate = (peak_tvoc - base_tvoc) / (ep_len - fire_start)
            for t in range(fire_start, ep_len):
                tvoc[t] = tvoc[t-1] + rate * np.random.uniform(0.85, 1.25)
                eco2[t] = min(15000.0, eco2[t-1] + np.random.uniform(400.0, 1200.0))
                temp[t] = min(82.0, temp[t-1] + np.random.uniform(2.5, 5.5))
                hum[t] = max(10.0, hum[t-1] - np.random.uniform(2.0, 4.0))
                press[t] = np.random.uniform(936.0, 939.0)
                pm25[t] = min(750.0, pm25[t-1] + np.random.uniform(25.0, 60.0))

        else: # cleared
            start_tvoc = np.random.uniform(10000.0, 18000.0)
            tvoc[0] = start_tvoc
            for t in range(1, ep_len):
                tvoc[t] = max(600.0, tvoc[t-1] - np.random.uniform(800.0, 1600.0))
            temp = np.random.uniform(25.0, 35.0, ep_len)
            hum = np.random.uniform(40.0, 55.0, ep_len)
            eco2 = np.random.uniform(600.0, 1200.0, ep_len)
            press = np.random.uniform(938.0, 940.0, ep_len)
            pm25 = np.random.uniform(10.0, 50.0, ep_len)

        temp = np.clip(temp, 0.0, 85.0)
        hum = np.clip(hum, 10.0, 80.0)
        tvoc = np.clip(tvoc, 0.0, 25000.0)
        eco2 = np.clip(eco2, 400.0, 15000.0)
        press = np.clip(press, 930.0, 945.0)
        pm25 = np.clip(pm25, 0.0, 800.0)

        data = np.column_stack([temp, hum, tvoc, eco2, press, pm25])

        for i in range(ep_len - seq_len - forecast_steps + 1):
            X_seq = data[i : i + seq_len]
            y_f = data[i + seq_len : i + seq_len + forecast_steps, 2] # future TVOC[ppb]
            risk = 1.0 if np.any(y_f >= 4000.0) else 0.0
            
            all_X.append(X_seq)
            all_y_reg.append(y_f)
            all_y_risk.append([risk])

    return np.array(all_X, dtype=np.float32), np.array(all_y_reg, dtype=np.float32), np.array(all_y_risk, dtype=np.float32)

def train_fire_gru():
    print("\n===========================================================")
    print("  [FIR3 Node] Training GRU Multi-Step Forecaster (Wildfire)")
    print("  Predicting Combustion Gas Density TVOC (t + 10m to t + 50m)")
    print("===========================================================")

    features = ['Temperature[C]', 'Humidity[%]', 'TVOC[ppb]', 'eCO2[ppm]', 'Pressure[hPa]', 'PM2.5']

    min_vals = {
        'Temperature[C]': 0.0,
        'Humidity[%]': 10.0,
        'TVOC[ppb]': 0.0,
        'eCO2[ppm]': 400.0,
        'Pressure[hPa]': 930.0,
        'PM2.5': 0.0
    }
    max_vals = {
        'Temperature[C]': 85.0,
        'Humidity[%]': 80.0,
        'TVOC[ppb]': 25000.0,
        'eCO2[ppm]': 15000.0,
        'Pressure[hPa]': 945.0,
        'PM2.5': 800.0
    }

    scaler_info = {
        "features": features,
        "target": "TVOC[ppb]",
        "target_idx": 2,
        "min": min_vals,
        "max": max_vals,
        "target_min": min_vals["TVOC[ppb]"],
        "target_max": max_vals["TVOC[ppb]"]
    }
    with open(os.path.join(MODELS_DIR, "fire_gru_scaler.json"), "w") as f:
        json.dump(scaler_info, f, indent=2)

    X, y_reg, y_risk = generate_fire_temporal_dataset(n_episodes=900)
    print(f"Generated {len(X)} temporal sequences from combustion profiles.")

    min_arr = np.array([min_vals[f] for f in features], dtype=np.float32)
    max_arr = np.array([max_vals[f] for f in features], dtype=np.float32)
    diff_arr = max_arr - min_arr

    X_norm = (X - min_arr) / diff_arr
    y_reg_norm = (y_reg - min_vals["TVOC[ppb]"]) / (max_vals["TVOC[ppb]"] - min_vals["TVOC[ppb]"])

    split_idx = int(0.8 * len(X))
    X_train, X_test = X_norm[:split_idx], X_norm[split_idx:]
    y_reg_train, y_reg_test = y_reg_norm[:split_idx], y_reg_norm[split_idx:]
    y_risk_train, y_risk_test = y_risk[:split_idx], y_risk[split_idx:]

    train_ds = TensorDataset(torch.from_numpy(X_train), torch.from_numpy(y_reg_train), torch.from_numpy(y_risk_train))
    test_ds = TensorDataset(torch.from_numpy(X_test), torch.from_numpy(y_reg_test), torch.from_numpy(y_risk_test))

    train_loader = DataLoader(train_ds, batch_size=64, shuffle=True)
    test_loader = DataLoader(test_ds, batch_size=64, shuffle=False)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = DisasterGRUForecaster(input_dim=len(features), hidden_dim=64, num_layers=2, forecast_steps=5, dropout=0.2).to(device)
    crit_reg = nn.MSELoss()
    crit_risk = nn.BCELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.004, weight_decay=1e-5)

    EPOCHS = 10
    for epoch in range(1, EPOCHS + 1):
        model.train()
        total_loss = 0.0
        for bx, byr, byk in train_loader:
            bx, byr, byk = bx.to(device), byr.to(device), byk.to(device)
            optimizer.zero_grad()
            pr, pk = model(bx)
            loss = crit_reg(pr, byr) + 0.6 * crit_risk(pk, byk)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        if epoch % 2 == 0 or epoch == EPOCHS:
            print(f"  Epoch [{epoch:02d}/{EPOCHS:02d}] -> Loss: {total_loss/len(train_loader):.4f}")

    model.eval()
    all_maes = []
    with torch.no_grad():
        for bx, byr, _ in test_loader:
            bx = bx.to(device)
            pr, _ = model(bx)
            pred_v = pr.cpu().numpy() * (max_vals["TVOC[ppb]"] - min_vals["TVOC[ppb]"]) + min_vals["TVOC[ppb]"]
            true_v = byr.numpy() * (max_vals["TVOC[ppb]"] - min_vals["TVOC[ppb]"]) + min_vals["TVOC[ppb]"]
            all_maes.append(np.mean(np.abs(pred_v - true_v)))

    print(f"\n[FIR3 GRU Performance] Mean Absolute Error (MAE): ±{np.mean(all_maes):.1f} ppb across 50-min horizon!")
    save_path = os.path.join(MODELS_DIR, "fire_gru.pth")
    torch.save(model.state_dict(), save_path)
    print(f"[SAVED] Trained Fire GRU saved to: {save_path}")


# ==============================================================================
# 4. AIR POLLUTION TEMPORAL SEQUENCE GENERATOR & TRAINER (POL4 Node)
# ==============================================================================

def generate_pollution_temporal_dataset(n_episodes=900, seq_len=10, forecast_steps=5):
    """
    Generates multi-step air pollution episodes:
    - 55% Clean to Moderate urban air (PM2.5: 5-25 µg/m³, NO2: 10-25 ppm)
    - 35% Winter temperature inversion / toxic smog buildup (PM2.5: 150-380 µg/m³)
    - 10% Wind clearing / post-smog dispersion
    """
    all_X, all_y_reg, all_y_risk = [], [], []

    for _ in range(n_episodes):
        ep_len = 30
        mode = np.random.choice(['clean', 'inversion', 'clearing'], p=[0.55, 0.35, 0.10])
        
        no2 = np.zeros(ep_len, dtype=np.float32)
        co = np.zeros(ep_len, dtype=np.float32)
        pm10 = np.zeros(ep_len, dtype=np.float32)
        pm25 = np.zeros(ep_len, dtype=np.float32)

        if mode == 'clean':
            no2 = np.random.uniform(8, 25, ep_len)
            co = np.random.uniform(0.5, 3.5, ep_len)
            pm10 = np.random.uniform(15, 45, ep_len)
            pm25 = np.random.uniform(5, 22, ep_len)

        elif mode == 'inversion':
            inv_start = np.random.randint(5, 10)
            no2[:inv_start] = np.random.uniform(15, 30, inv_start)
            co[:inv_start] = np.random.uniform(1.5, 4.0, inv_start)
            pm10[:inv_start] = np.random.uniform(30, 60, inv_start)
            pm25[:inv_start] = np.random.uniform(15, 35, inv_start)

            surge_len = ep_len - inv_start
            t = np.linspace(0, 1, surge_len)
            no2[inv_start:] = no2[inv_start-1] + 120.0 * (t ** 1.3) + np.random.normal(0, 3.0, surge_len)
            co[inv_start:] = co[inv_start-1] + 45.0 * (t ** 1.4) + np.random.normal(0, 1.2, surge_len)
            pm10[inv_start:] = pm10[inv_start-1] + 380.0 * (t ** 1.2) + np.random.normal(0, 8.0, surge_len)
            pm25[inv_start:] = pm25[inv_start-1] + 280.0 * (t ** 1.2) + np.random.normal(0, 6.0, surge_len)

        elif mode == 'clearing':
            no2 = np.linspace(95, 15, ep_len) + np.random.normal(0, 2.0, ep_len)
            co = np.linspace(35, 1.5, ep_len) + np.random.normal(0, 0.5, ep_len)
            pm10 = np.linspace(320, 25, ep_len) + np.random.normal(0, 5.0, ep_len)
            pm25 = np.linspace(240, 12, ep_len) + np.random.normal(0, 4.0, ep_len)

        # Clip values
        no2 = np.clip(no2, 0.0, 200.0)
        co = np.clip(co, 0.0, 70.0)
        pm10 = np.clip(pm10, 0.0, 550.0)
        pm25 = np.clip(pm25, 0.0, 400.0)

        episode_matrix = np.column_stack([no2, co, pm10, pm25])

        for start in range(0, ep_len - seq_len - forecast_steps + 1):
            x_seq = episode_matrix[start : start + seq_len]
            y_future = episode_matrix[start + seq_len : start + seq_len + forecast_steps, 3] # pm25
            breach = 1.0 if np.max(y_future) >= 150.0 else 0.0 # PM2.5 Severe/Emergency breach threshold

            all_X.append(x_seq)
            all_y_reg.append(y_future)
            all_y_risk.append([breach])

    return np.array(all_X, dtype=np.float32), np.array(all_y_reg, dtype=np.float32), np.array(all_y_risk, dtype=np.float32)

def train_pollution_gru(epochs=10):
    print("\n" + "=" * 65)
    print("  [POL4 Node] Training PyTorch GRU Forecaster (Severe Smog/AQI)")
    print("=" * 65)

    features = ['no2', 'co', 'pm10', 'pm25']
    min_vals = {
        'no2': 0.0,
        'co': 0.0,
        'pm10': 0.0,
        'pm25': 0.0
    }
    max_vals = {
        'no2': 200.0,
        'co': 70.0,
        'pm10': 550.0,
        'pm25': 400.0
    }

    scaler_info = {
        "features": features,
        "target": "pm25",
        "target_idx": 3,
        "min": min_vals,
        "max": max_vals,
        "target_min": min_vals["pm25"],
        "target_max": max_vals["pm25"]
    }
    with open(os.path.join(MODELS_DIR, "pollution_gru_scaler.json"), "w") as f:
        json.dump(scaler_info, f, indent=2)

    X, y_reg, y_risk = generate_pollution_temporal_dataset(n_episodes=900)
    print(f"Generated {len(X)} temporal sequences from air quality profiles.")

    min_arr = np.array([min_vals[f] for f in features], dtype=np.float32)
    max_arr = np.array([max_vals[f] for f in features], dtype=np.float32)
    diff_arr = max_arr - min_arr

    X_norm = (X - min_arr) / diff_arr
    y_reg_norm = (y_reg - min_vals["pm25"]) / (max_vals["pm25"] - min_vals["pm25"])

    split_idx = int(0.8 * len(X))
    X_train, X_test = X_norm[:split_idx], X_norm[split_idx:]
    y_reg_train, y_reg_test = y_reg_norm[:split_idx], y_reg_norm[split_idx:]
    y_risk_train, y_risk_test = y_risk[:split_idx], y_risk[split_idx:]

    train_ds = TensorDataset(torch.from_numpy(X_train), torch.from_numpy(y_reg_train), torch.from_numpy(y_risk_train))
    test_ds = TensorDataset(torch.from_numpy(X_test), torch.from_numpy(y_reg_test), torch.from_numpy(y_risk_test))

    train_loader = DataLoader(train_ds, batch_size=64, shuffle=True)
    test_loader = DataLoader(test_ds, batch_size=64, shuffle=False)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = DisasterGRUForecaster(input_dim=len(features), hidden_dim=64, num_layers=2, forecast_steps=5, dropout=0.2).to(device)
    crit_reg = nn.MSELoss()
    crit_risk = nn.BCELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.004, weight_decay=1e-5)

    EPOCHS = 10
    for epoch in range(1, EPOCHS + 1):
        model.train()
        total_loss = 0.0
        for bx, byr, byk in train_loader:
            bx, byr, byk = bx.to(device), byr.to(device), byk.to(device)
            optimizer.zero_grad()
            pr, pk = model(bx)
            loss = crit_reg(pr, byr) + 0.6 * crit_risk(pk, byk)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        if epoch % 2 == 0 or epoch == EPOCHS:
            print(f"  Epoch [{epoch:02d}/{EPOCHS:02d}] -> Loss: {total_loss/len(train_loader):.4f}")

    model.eval()
    all_maes = []
    with torch.no_grad():
        for bx, byr, _ in test_loader:
            bx = bx.to(device)
            pr, _ = model(bx)
            pred_v = pr.cpu().numpy() * (max_vals["pm25"] - min_vals["pm25"]) + min_vals["pm25"]
            true_v = byr.numpy() * (max_vals["pm25"] - min_vals["pm25"]) + min_vals["pm25"]
            all_maes.append(np.mean(np.abs(pred_v - true_v)))

    print(f"\n[POL4 GRU Performance] Mean Absolute Error (MAE): ±{np.mean(all_maes):.2f} µg/m³ across 50-min horizon!")
    save_path = os.path.join(MODELS_DIR, "pollution_gru.pth")
    torch.save(model.state_dict(), save_path)
    print(f"[SAVED] Trained Pollution GRU saved to: {save_path}")


if __name__ == "__main__":
    train_flood_gru()
    train_landslide_gru()
    train_fire_gru()
    train_pollution_gru()


