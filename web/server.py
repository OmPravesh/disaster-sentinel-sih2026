import os
import sys
import time
from datetime import datetime
import json
import numpy as np
import torch
import joblib
import pandas as pd
from flask import Flask, jsonify, render_template, request, redirect, url_for

# Set up paths relative to project root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "ai"))

# Import GRU Model Definition
try:
    from ai.model_gru import DisasterGRUForecaster
except ImportError:
    try:
        from model_gru import DisasterGRUForecaster
    except ImportError:
        from src.model_gru import DisasterGRUForecaster

# Ensure UTF-8 output encoding for Windows PowerShell / CMD
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)

# Enable Cross-Origin Resource Sharing (CORS) for VS Code Live Preview (port 3000)
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response

# -------------------------------------------------------------
# 1. LOAD TRAINED ML MODELS (Brain 1: Random Forest)
# -------------------------------------------------------------
MODELS_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, "models"))
models = {}

def load_ml_models():
    hazard_models = {
        "fire": "fire_model.joblib",
        "pollution": "pollution_model.joblib",
        "flood": "flood_model.joblib",
        "landslide": "landslide_model.joblib"
    }
    for hazard, filename in hazard_models.items():
        path = os.path.join(MODELS_DIR, filename)
        if os.path.exists(path):
            try:
                models[hazard] = joblib.load(path)
                print(f"[OK] Loaded {hazard.upper()} Random Forest model from: {path}")
            except Exception as e:
                print(f"[WARN] Error loading {hazard} model: {e}")
        else:
            print(f"[WARN] Model file not found: {path}")

load_ml_models()

# -------------------------------------------------------------
# 1B. LOAD PYTORCH GRU FORECASTERS (Brain 2: Jetson Deep Learning)
# -------------------------------------------------------------
gru_models = {}
gru_scalers = {}

def load_gru_models():
    # Flood GRU (FLD1)
    f_weights = os.path.join(MODELS_DIR, "flood_gru.pth")
    f_scaler = os.path.join(MODELS_DIR, "flood_gru_scaler.json")
    if os.path.exists(f_weights) and os.path.exists(f_scaler):
        try:
            with open(f_scaler, "r") as f:
                gru_scalers["FLD1"] = json.load(f)
            model = DisasterGRUForecaster(
                input_dim=len(gru_scalers["FLD1"]["features"]),
                hidden_dim=64,
                num_layers=2,
                forecast_steps=5
            )
            model.load_state_dict(torch.load(f_weights, map_location=torch.device('cpu')))
            model.eval()
            gru_models["FLD1"] = model
            print(f"[OK] Loaded FLOOD PyTorch GRU Forecaster on Jetson Orin Nano Hub!")
        except Exception as e:
            print(f"[WARN] Loading Flood GRU: {e}")

    # Landslide GRU (SLD2)
    l_weights = os.path.join(MODELS_DIR, "landslide_gru.pth")
    l_scaler = os.path.join(MODELS_DIR, "landslide_gru_scaler.json")
    if os.path.exists(l_weights) and os.path.exists(l_scaler):
        try:
            with open(l_scaler, "r") as f:
                gru_scalers["SLD2"] = json.load(f)
            model = DisasterGRUForecaster(
                input_dim=len(gru_scalers["SLD2"]["features"]),
                hidden_dim=64,
                num_layers=2,
                forecast_steps=5
            )
            model.load_state_dict(torch.load(l_weights, map_location=torch.device('cpu')))
            model.eval()
            gru_models["SLD2"] = model
            print(f"[OK] Loaded LANDSLIDE PyTorch GRU Forecaster on Jetson Orin Nano Hub!")
        except Exception as e:
            print(f"[WARN] Loading Landslide GRU: {e}")

    # Wildfire GRU (FIR3)
    fi_weights = os.path.join(MODELS_DIR, "fire_gru.pth")
    fi_scaler = os.path.join(MODELS_DIR, "fire_gru_scaler.json")
    if os.path.exists(fi_weights) and os.path.exists(fi_scaler):
        try:
            with open(fi_scaler, "r") as f:
                gru_scalers["FIR3"] = json.load(f)
            model = DisasterGRUForecaster(
                input_dim=len(gru_scalers["FIR3"]["features"]),
                hidden_dim=64,
                num_layers=2,
                forecast_steps=5
            )
            model.load_state_dict(torch.load(fi_weights, map_location=torch.device('cpu')))
            model.eval()
            gru_models["FIR3"] = model
            print(f"[OK] Loaded WILDFIRE PyTorch GRU Forecaster on Jetson Orin Nano Hub!")
        except Exception as e:
            print(f"[WARN] Loading Wildfire GRU: {e}")

    # Pollution / Toxic Smog GRU (POL4)
    p_weights = os.path.join(MODELS_DIR, "pollution_gru.pth")
    p_scaler = os.path.join(MODELS_DIR, "pollution_gru_scaler.json")
    if os.path.exists(p_weights) and os.path.exists(p_scaler):
        try:
            with open(p_scaler, "r") as f:
                gru_scalers["POL4"] = json.load(f)
            model = DisasterGRUForecaster(
                input_dim=len(gru_scalers["POL4"]["features"]),
                hidden_dim=64,
                num_layers=2,
                forecast_steps=5
            )
            model.load_state_dict(torch.load(p_weights, map_location=torch.device('cpu')))
            model.eval()
            gru_models["POL4"] = model
            print(f"[OK] Loaded POLLUTION PyTorch GRU Forecaster on Jetson Orin Nano Hub!")
        except Exception as e:
            print(f"[WARN] Loading Pollution GRU: {e}")

load_gru_models()

# Rolling sequence buffer for all 4 GRU temporal inputs (maintains last 10 observations)
node_sequence_buffers = {
    "FLD1": [],
    "SLD2": [],
    "FIR3": [],
    "POL4": []
}

def seed_sequence_buffers():
    node_sequence_buffers["FLD1"] = [
        {"River_Water_Level_m": round(2.05 + 0.01 * i, 2), "Rainfall_mm": 12.0, "Rainfall_Intensity_mm_hr": 1.5, "Atmospheric_Pressure_hPa": 1005.4, "Temperature_C": 31.5, "Relative_Humidity_pct": 78.0}
        for i in range(10)
    ]
    node_sequence_buffers["SLD2"] = [
        {"Slope_Angle": round(11.8 + 0.05 * i, 2), "Soil_Saturation": 0.15, "Rainfall_mm": 10.0, "Temperature_C": 22.0, "Humidity_percent": 45.0}
        for i in range(10)
    ]
    node_sequence_buffers["FIR3"] = [
        {"Temperature[C]": round(22.0 + 0.05 * i, 1), "Humidity[%]": 52.0, "TVOC[ppb]": round(20.0 + 0.5 * i, 1), "eCO2[ppm]": 415.0, "Pressure[hPa]": 939.5, "PM2.5": 0.8}
        for i in range(10)
    ]
    node_sequence_buffers["POL4"] = [
        {"no2": round(14.0 + 0.1 * i, 1), "co": 2.1, "pm10": 42.0, "pm25": round(11.0 + 0.1 * i, 1)}
        for i in range(10)
    ]

seed_sequence_buffers()

# -------------------------------------------------------------
# 2. SYSTEM & NODE STATE MANAGEMENT
# -------------------------------------------------------------
hub_state = {
    "hub_id": "JETSON-ORIN-NANO-01",
    "hub_name": "NVIDIA Jetson Orin Nano (Central Hub)",
    "processor": "6-core ARM v8.2 64-bit | 1024-core Ampere GPU",
    "lora_protocol": "SX1278 LoRa SPI0 @ 433.0 MHz",
    "lora_status": "ONLINE",
    "gsm_status": "ONLINE (SIM800L RSSI: 28/31)",
    "buzzer_gpio18": False,
    "strobe_gpio23": False,
    "last_sync": datetime.now().strftime("%H:%M:%S"),
    "active_alerts_count": 0
}

# Baseline safe telemetry for the 4 nodes
node_states = {
    "FLD1": {
        "node_id": "FLD1",
        "name": "Flood Monitoring Node",
        "hazard": "Flood",
        "location": "Rishikesh · Ganga River Basin Catchment, Uttarakhand",
        "gps": {"lat": 30.0869, "lng": 78.2676},
        "status": "Safe",
        "battery": 95,
        "lora_rssi": -68,
        "sensors": {
            "River_Water_Level_m": 2.10,
            "Rainfall_mm": 12.24,
            "Rainfall_Intensity_mm_hr": 1.54,
            "Atmospheric_Pressure_hPa": 1005.40,
            "Temperature_C": 31.5,
            "Relative_Humidity_pct": 78.0
        },
        "units": {
            "River_Water_Level_m": "m",
            "Rainfall_mm": "mm",
            "Rainfall_Intensity_mm_hr": "mm/h",
            "Atmospheric_Pressure_hPa": "hPa",
            "Temperature_C": "°C",
            "Relative_Humidity_pct": "%"
        },
        "hardware_layers": "Layer 1: HC-SR04/JSN-SR04T | Layer 2: YL-83 | Layer 3: BME280"
    },
    "SLD2": {
        "node_id": "SLD2",
        "name": "Landslide Monitoring Node",
        "hazard": "Landslide",
        "location": "Chamoli · Garhwal Mountain Slope Sector 2B, Uttarakhand",
        "gps": {"lat": 30.3844, "lng": 79.2811},
        "status": "Safe",
        "risk_prob": 0.0,
        "battery": 89,
        "lora_rssi": -72,
        "sensors": {
            "Slope_Angle": 12.0,
            "Soil_Saturation": 0.15,
            "Rainfall_mm": 10.0,
            "Temperature_C": 22.0,
            "Humidity_percent": 45.0
        },
        "units": {
            "Slope_Angle": "°",
            "Soil_Saturation": "fraction",
            "Rainfall_mm": "mm",
            "Temperature_C": "°C",
            "Humidity_percent": "%"
        },
        "hardware_layers": "Layer 1: MPU6050 Gyro/Tilt | Layer 2: Soil Moisture v1.2 | Layer 3: BME280"
    },
    "FIR3": {
        "node_id": "FIR3",
        "name": "Fire Monitoring Node",
        "hazard": "Fire",
        "location": "Almora · Kumaon Pine Forest Perimeter, Uttarakhand",
        "gps": {"lat": 29.6200, "lng": 79.6800},
        "status": "Safe",
        "battery": 92,
        "lora_rssi": -65,
        "sensors": {
            "Temperature[C]": 22.5,
            "Humidity[%]": 52.0,
            "TVOC[ppb]": 25.0,
            "eCO2[ppm]": 415.0,
            "Raw H2": 12300.0,
            "Raw Ethanol": 18550.0,
            "Pressure[hPa]": 939.5,
            "PM1.0": 0.5,
            "PM2.5": 0.8,
            "NC0.5": 0.5,
            "NC1.0": 0.1,
            "NC2.5": 0.01
        },
        "units": {
            "Temperature[C]": "°C",
            "Humidity[%]": "%",
            "TVOC[ppb]": "ppb",
            "eCO2[ppm]": "ppm",
            "Pressure[hPa]": "hPa",
            "PM2.5": "µg/m³"
        },
        "hardware_layers": "Layer 1: KY-026 Flame IR | Layer 2: MQ-2 Gas/Smoke | Layer 3: BME280"
    },
    "POL4": {
        "node_id": "POL4",
        "name": "Air Quality Monitoring Node",
        "hazard": "Pollution",
        "location": "Dehradun · Selaqui Valley Industrial Corridor, Uttarakhand",
        "gps": {"lat": 30.3400, "lng": 77.8700},
        "status": "Safe",
        "battery": 87,
        "lora_rssi": -70,
        "sensors": {
            "no2": 14.5,
            "co": 2.1,
            "pm10": 42.0,
            "pm25": 11.5
        },
        "units": {
            "no2": "ppm",
            "co": "ppm",
            "pm10": "µg/m³",
            "pm25": "µg/m³"
        },
        "hardware_layers": "Layer 1: MQ-135 Gas | Layer 2: GP2Y1010AU0F Optical Dust"
    }
}

# Real-time history ring buffer for time-series charts (last 20 points)
history_log = []

def record_history():
    now_str = datetime.now().strftime("%H:%M:%S")
    entry = {
        "time": now_str,
        "fld1_water": node_states["FLD1"]["sensors"]["River_Water_Level_m"],
        "fld1_rain": node_states["FLD1"]["sensors"]["Rainfall_mm"],
        "sld2_slope": node_states["SLD2"]["sensors"]["Slope_Angle"],
        "sld2_soil": node_states["SLD2"]["sensors"]["Soil_Saturation"] * 100,
        "pol4_pm25": node_states["POL4"]["sensors"]["pm25"],
        "pol4_no2": node_states["POL4"]["sensors"]["no2"],
        "fir3_temp": node_states["FIR3"]["sensors"]["Temperature[C]"],
        "fir3_smoke": node_states["FIR3"]["sensors"]["TVOC[ppb]"]
    }
    history_log.append(entry)
    if len(history_log) > 20:
        history_log.pop(0)

# Incident history log for NDRF Operations and Incident Management
incident_log = [
    {
        "id": "INC-101",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "node_id": "SYS",
        "hazard": "System",
        "title": "Autonomous Edge Hub Boot Sequence",
        "severity": "INFO",
        "status": "Resolved",
        "details": "NVIDIA Jetson Orin Nano AI Hub initialized. LoRa SX1278 SPI link online @ 433.0 MHz."
    }
]

# Initialize with a few seed points so charts render immediately
for _ in range(5):
    record_history()

def update_hub_alert_status():
    """Syncs buzzer and strobe states with active hazardous alerts."""
    hazardous = [n for n in node_states.values() if n["status"] == "Hazardous"]
    warnings = [n for n in node_states.values() if n["status"] == "Warning"]
    
    hub_state["active_alerts_count"] = len(hazardous) + len(warnings)
    hub_state["last_sync"] = datetime.now().strftime("%H:%M:%S")
    
    if len(hazardous) > 0:
        hub_state["buzzer_gpio18"] = True
        hub_state["strobe_gpio23"] = True
    else:
        hub_state["buzzer_gpio18"] = False
        hub_state["strobe_gpio23"] = False

# -------------------------------------------------------------
# 3. REST API ENDPOINTS
# -------------------------------------------------------------

def run_gru_forecast(node_id):
    """
    Executes PyTorch GRU multi-step future forecasting on NVIDIA Jetson Orin Nano.
    Takes sliding sequence window (10 observations) and projects:
    - 5 future timesteps (+10m, +20m, +30m, +40m, +50m)
    - Future disaster breach probability P(Hazardous at t+30m)
    - Early Warning Lead Time (mins before threshold breach)
    """
    if node_id not in gru_models or node_id not in gru_scalers:
        return {"success": False, "error": f"No GRU model registered for node {node_id}"}
    
    scaler = gru_scalers[node_id]
    model = gru_models[node_id]
    features = scaler["features"]
    
    buf = node_sequence_buffers.get(node_id, [])
    if len(buf) < 10:
        seed_sequence_buffers()
        buf = node_sequence_buffers.get(node_id, [])
        
    recent_seq = buf[-10:]
    norm_rows = []
    for row in recent_seq:
        vec = []
        for f in features:
            val = float(row.get(f, scaler["min"][f]))
            min_v = float(scaler["min"][f])
            max_v = float(scaler["max"][f])
            diff = max_v - min_v
            norm_v = (val - min_v) / (diff if diff != 0 else 1.0)
            vec.append(norm_v)
        norm_rows.append(vec)
        
    x_tensor = torch.tensor([norm_rows], dtype=torch.float32)
    with torch.no_grad():
        pred_reg, pred_risk = model(x_tensor)
        
    target_min = float(scaler["target_min"])
    target_max = float(scaler["target_max"])
    denorm_future = pred_reg[0].cpu().numpy() * (target_max - target_min) + target_min
    future_vals = [round(float(v), 2) for v in denorm_future]
    risk_pct = round(float(pred_risk[0][0]) * 100, 1)
    
    if node_id == "FLD1":
        target_name = "River Water Level"
        unit = "m"
        warn_th = 6.0
        crit_th = 10.0
    elif node_id == "SLD2":
        target_name = "Slope Incline Angle"
        unit = "°"
        warn_th = 30.0
        crit_th = 45.0
    elif node_id == "FIR3":
        target_name = "Combustion Gas Density"
        unit = "ppb"
        warn_th = 1500.0
        crit_th = 5000.0
    elif node_id == "POL4":
        target_name = "PM2.5 Particulate Dust"
        unit = "µg/m³"
        warn_th = 60.0
        crit_th = 150.0
    else:
        target_name = "Sensor Metric"
        unit = ""
        warn_th = 50.0
        crit_th = 100.0
        
    crit_step = next((i for i, v in enumerate(future_vals) if v >= crit_th), None)
    warn_step = next((i for i, v in enumerate(future_vals) if v >= warn_th), None)
    
    if crit_step is not None:
        lead_time_min = (crit_step + 1) * 10
        threat_level = "CRITICAL"
        lead_time_label = f"BREACH PREDICTED IN {lead_time_min} MINS"
    elif warn_step is not None:
        lead_time_min = (warn_step + 1) * 10
        threat_level = "WARNING"
        lead_time_label = f"SURGE PROJECTED IN {lead_time_min} MINS"
    else:
        lead_time_min = None
        threat_level = "SAFE"
        lead_time_label = "NORMAL (50+ MIN HORIZON SAFE)"
        
    steps_data = [
        {"step": f"+{(i+1)*10}m", "time_min": (i+1)*10, "predicted_value": future_vals[i]}
        for i in range(len(future_vals))
    ]
    
    target_key = scaler["target"]
    history_vals = [round(float(r.get(target_key, 0)), 2) for r in recent_seq]
    
    hazards_map = {
        "FLD1": "Flood",
        "SLD2": "Landslide",
        "FIR3": "Wildfire",
        "POL4": "Air Pollution"
    }

    return {
        "success": True,
        "node_id": node_id,
        "hazard": hazards_map.get(node_id, "Hazard"),
        "target_name": target_name,
        "unit": unit,
        "thresholds": {"warning": warn_th, "critical": crit_th},
        "history_values": history_vals,
        "current_value": history_vals[-1] if history_vals else 0,
        "future_steps": steps_data,
        "forecast_horizon_min": 50,
        "risk_probability_pct": risk_pct,
        "threat_level": threat_level,
        "lead_time_minutes": lead_time_min,
        "lead_time_label": lead_time_label,
        "ai_engine": "DisasterGRUForecaster (PyTorch 2.14 on NVIDIA Jetson Orin Nano)"
    }

# -------------------------------------------------------------
# 3. PAGE VIEW ROUTES (Clean 7-Page Enterprise Platform Architecture)
# -------------------------------------------------------------

@app.route("/")
def overview_page():
    """Page 1 — Overview: 5-second executive situational awareness."""
    return render_template("overview.html", active_page="overview")

@app.route("/monitoring")
def monitoring_page():
    """Page 2 — Live Monitoring: Dedicated 4-disaster telemetry & risk tracking."""
    return render_template("monitoring.html", active_page="monitoring")

@app.route("/map")
def map_page():
    """Page 3 — Disaster Map: GIS spatial risk zones & active incidents."""
    api_key = os.environ.get("MAP_API_KEY", "")
    return render_template("map.html", active_page="map", map_api_key=api_key)

@app.route("/alerts")
def alerts_page():
    """Page 4 — Alerts & Emergency: Prioritized alerts & NDRF SOS dispatch."""
    return render_template("alerts.html", active_page="alerts")

@app.route("/analytics")
def analytics_page():
    """Page 5 — Analytics & ML: Multi-step GRU predictions & model evaluation."""
    return render_template("analytics.html", active_page="analytics")

@app.route("/hardware")
def hardware_page():
    """Page 6 — IoT Hardware: ESP32 nodes, LoRa SPI, GPIOs, & diagnostics."""
    return render_template("hardware.html", active_page="hardware")

@app.route("/about")
def about_page():
    """Page 7 — About / System: Architecture, data pipeline, & SIH 2026 specs."""
    return render_template("about.html", active_page="about")

# Backward Compatibility Aliases & Redirects
@app.route("/nodes")
def redirect_nodes():
    return redirect(url_for('monitoring_page'))

@app.route("/forecast")
def redirect_forecast():
    return redirect(url_for('analytics_page'))

@app.route("/incidents")
def redirect_incidents():
    return redirect(url_for('alerts_page'))

@app.route("/legacy")
def legacy_page():
    """Preserves access to the legacy single-page dashboard."""
    return render_template("index.html", active_page="legacy")

# -------------------------------------------------------------
# 4. REST API DATA ENDPOINTS
# -------------------------------------------------------------

@app.route("/api/incidents", methods=["GET"])
def get_incidents():
    """Returns chronological disaster incident history log."""
    return jsonify({
        "success": True,
        "incidents": incident_log
    })

@app.route("/api/nodes", methods=["GET"])
def get_nodes():
    """Returns real-time telemetry, node health, and hub status."""
    return jsonify({
        "success": True,
        "hub": hub_state,
        "nodes": node_states
    })

@app.route("/api/history", methods=["GET"])
def get_history():
    """Returns telemetry history for Chart.js trend lines."""
    return jsonify({
        "success": True,
        "history": history_log
    })

@app.route("/api/forecast/<node_id>", methods=["GET"])
def get_node_forecast(node_id):
    """Returns Jetson GRU 5-step future forecast and early lead-time for specific node."""
    res = run_gru_forecast(node_id.upper())
    return jsonify(res)

@app.route("/api/forecast", methods=["GET"])
def get_all_forecasts():
    """Returns forecasts for all 4 deep-learning enabled edge nodes (FLD1, SLD2, FIR3, POL4)."""
    return jsonify({
        "success": True,
        "forecasts": {
            "FLD1": run_gru_forecast("FLD1"),
            "SLD2": run_gru_forecast("SLD2"),
            "FIR3": run_gru_forecast("FIR3"),
            "POL4": run_gru_forecast("POL4")
        }
    })

@app.route("/api/actuators/<device>/toggle", methods=["POST"])
def toggle_actuator(device):
    """Allows manual override of Jetson GPIO18 Buzzer or GPIO23 Strobe."""
    if device == "buzzer":
        hub_state["buzzer_gpio18"] = not hub_state["buzzer_gpio18"]
        state = hub_state["buzzer_gpio18"]
    elif device == "strobe":
        hub_state["strobe_gpio23"] = not hub_state["strobe_gpio23"]
        state = hub_state["strobe_gpio23"]
    else:
        return jsonify({"success": False, "error": "Unknown device"}), 400
        
    return jsonify({
        "success": True,
        "device": device,
        "state": state
    })

@app.route("/api/simulate/<scenario>", methods=["POST"])
def simulate_scenario(scenario):
    """
    SIH Presentation Endpoint:
    Triggers simulated disaster events on hardware nodes and executes live ML inference!
    """
    scenario = scenario.lower()
    
    if scenario == "flash_flood":
        node = node_states["FLD1"]
        node["sensors"]["River_Water_Level_m"] = 13.25
        node["sensors"]["Rainfall_mm"] = 275.40
        node["sensors"]["Rainfall_Intensity_mm_hr"] = 52.10
        node["sensors"]["Atmospheric_Pressure_hPa"] = 979.40
        node["sensors"]["Temperature_C"] = 17.2
        node["sensors"]["Relative_Humidity_pct"] = 96.0
        
        # Update GRU sequence buffer with surge trajectory
        node_sequence_buffers["FLD1"] = [
            {
                "River_Water_Level_m": round(2.5 + 1.15 * i, 2),
                "Rainfall_mm": round(45.0 + 24.5 * i, 1),
                "Rainfall_Intensity_mm_hr": round(6.0 + 4.8 * i, 1),
                "Atmospheric_Pressure_hPa": round(1005.0 - 2.7 * i, 1),
                "Temperature_C": round(30.0 - 1.3 * i, 1),
                "Relative_Humidity_pct": round(75.0 + 2.2 * i, 1)
            }
            for i in range(10)
        ]
        
        # Run Random Forest Tripwire
        if "flood" in models:
            df = pd.DataFrame([node["sensors"]])
            pred = models["flood"].predict(df)[0]
            node["status"] = pred
        else:
            node["status"] = "Hazardous"
            
        incident_log.insert(0, {
            "id": f"INC-{len(incident_log)+101}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "node_id": "FLD1",
            "hazard": "Flood",
            "title": "Rishikesh Ganga River Surge Detected",
            "severity": "CRITICAL",
            "status": "Active",
            "details": "Water level jumped to 13.25m at Rishikesh Ganga Catchment Station #4 (Critical > 10.0m). GRU forecaster projects breach in 10 mins."
        })

    elif scenario == "landslide_collapse":
        node = node_states["SLD2"]
        node["sensors"]["Slope_Angle"] = 58.5
        node["sensors"]["Soil_Saturation"] = 0.86
        node["sensors"]["Rainfall_mm"] = 168.0
        node["sensors"]["Temperature_C"] = 14.2
        node["sensors"]["Humidity_percent"] = 93.0
        
        # Update GRU sequence buffer with landslide slope tilt trajectory
        node_sequence_buffers["SLD2"] = [
            {
                "Slope_Angle": round(12.0 + 4.9 * i, 1),
                "Soil_Saturation": round(0.18 + 0.072 * i, 2),
                "Rainfall_mm": round(15.0 + 16.2 * i, 1),
                "Temperature_C": round(22.0 - 0.8 * i, 1),
                "Humidity_percent": round(48.0 + 4.8 * i, 1)
            }
            for i in range(10)
        ]
        
        if "landslide" in models:
            df = pd.DataFrame([node["sensors"]])
            prob = models["landslide"].predict_proba(df)[0][list(models["landslide"].classes_).index('Hazardous')]
            node["risk_prob"] = round(prob * 100, 1)
            node["status"] = "Hazardous" if prob >= 0.70 else ("Warning" if prob >= 0.35 else "Safe")
        else:
            node["status"] = "Hazardous"
            node["risk_prob"] = 98.4

        incident_log.insert(0, {
            "id": f"INC-{len(incident_log)+101}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "node_id": "SLD2",
            "hazard": "Landslide",
            "title": "Chamoli Garhwal Slope Shear Failure",
            "severity": "CRITICAL",
            "status": "Active",
            "details": "Chamoli slope tilt angle accelerated to 58.5°. Soil saturation at 86%. Rapid downslope displacement imminent."
        })

    elif scenario == "forest_fire":
        node = node_states["FIR3"]
        node["sensors"]["Temperature[C]"] = 78.4
        node["sensors"]["Humidity[%]"] = 14.2
        node["sensors"]["TVOC[ppb]"] = 18450
        node["sensors"]["eCO2[ppm]"] = 4210
        node["sensors"]["Raw H2"] = 12800.0
        node["sensors"]["Raw Ethanol"] = 19500.0
        node["sensors"]["Pressure[hPa]"] = 939.1
        node["sensors"]["PM1.0"] = 25.0
        node["sensors"]["PM2.5"] = 385.0
        node["sensors"]["NC0.5"] = 120.0
        node["sensors"]["NC1.0"] = 45.0
        node["sensors"]["NC2.5"] = 8.0
        
        # Update GRU sequence buffer with smoldering combustion surge trajectory
        node_sequence_buffers["FIR3"] = [
            {
                "Temperature[C]": round(25.0 + 5.5 * i, 1),
                "Humidity[%]": round(50.0 - 3.8 * i, 1),
                "TVOC[ppb]": round(800.0 + 1850.0 * i, 1),
                "eCO2[ppm]": round(717.0 + 380.0 * i, 1),
                "Pressure[hPa]": round(939.1 - 0.3 * i, 1),
                "PM2.5": round(2.5 + 40.0 * i, 1)
            }
            for i in range(10)
        ]
        
        if "fire" in models:
            df = pd.DataFrame([node["sensors"]])
            pred = models["fire"].predict(df)[0]
            node["status"] = "Hazardous" if pred == 1 else "Safe"
        else:
            node["status"] = "Hazardous"

        incident_log.insert(0, {
            "id": f"INC-{len(incident_log)+101}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "node_id": "FIR3",
            "hazard": "Wildfire",
            "title": "Almora Kumaon Pine Forest Wildfire",
            "severity": "CRITICAL",
            "status": "Active",
            "details": "Combustion gas TVOC spiked to 18,450 ppb in Almora Pine Forest Reserve. Ambient temperature 78.4°C. Flame sensor tripwire positive."
        })

    elif scenario == "toxic_smog":
        node = node_states["POL4"]
        node["sensors"]["no2"] = 96.5
        node["sensors"]["co"] = 39.2
        node["sensors"]["pm10"] = 460.0
        node["sensors"]["pm25"] = 275.0
        
        # Update GRU sequence buffer with industrial smog inversion surge trajectory
        node_sequence_buffers["POL4"] = [
            {
                "no2": round(14.5 + 8.5 * i, 1),
                "co": round(2.1 + 3.8 * i, 1),
                "pm10": round(42.0 + 42.5 * i, 1),
                "pm25": round(11.5 + 27.5 * i, 1)
            }
            for i in range(10)
        ]
        
        if "pollution" in models:
            df = pd.DataFrame([node["sensors"]])
            pred = models["pollution"].predict(df)[0]
            node["status"] = pred
        else:
            node["status"] = "Hazardous"

        incident_log.insert(0, {
            "id": f"INC-{len(incident_log)+101}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "node_id": "POL4",
            "hazard": "Air Pollution",
            "title": "Dehradun Selaqui Valley Severe Smog Inversion",
            "severity": "CRITICAL",
            "status": "Active",
            "details": "Particulate dust PM2.5 jumped to 275 µg/m³ in Dehradun Selaqui Industrial Corridor (Severe Hazardous > 150 µg/m³). Atmospheric inversion layer trapped pollutants."
        })

    elif scenario == "all_clear":
        seed_sequence_buffers()
        
        # Reset FLD1
        node_states["FLD1"]["sensors"] = {
            "River_Water_Level_m": 2.10, "Rainfall_mm": 12.24, "Rainfall_Intensity_mm_hr": 1.54,
            "Atmospheric_Pressure_hPa": 1005.40, "Temperature_C": 31.5, "Relative_Humidity_pct": 78.0
        }
        node_states["FLD1"]["status"] = "Safe"
        
        # Reset SLD2
        node_states["SLD2"]["sensors"] = {
            "Slope_Angle": 12.0, "Soil_Saturation": 0.15, "Rainfall_mm": 10.0,
            "Temperature_C": 22.0, "Humidity_percent": 45.0
        }
        node_states["SLD2"]["risk_prob"] = 0.0
        node_states["SLD2"]["status"] = "Safe"
        
        # Reset FIR3
        node_states["FIR3"]["sensors"] = {
            "Temperature[C]": 22.5, "Humidity[%]": 52.0, "TVOC[ppb]": 25.0, "eCO2[ppm]": 415.0,
            "Raw H2": 12300.0, "Raw Ethanol": 18550.0, "Pressure[hPa]": 939.5, "PM1.0": 0.5,
            "PM2.5": 0.8, "NC0.5": 0.5, "NC1.0": 0.1, "NC2.5": 0.01
        }
        node_states["FIR3"]["status"] = "Safe"
        
        # Reset POL4
        node_states["POL4"]["sensors"] = {
            "no2": 14.5, "co": 2.1, "pm10": 42.0, "pm25": 11.5
        }
        node_states["POL4"]["status"] = "Safe"

        for inc in incident_log:
            if inc["status"] == "Active":
                inc["status"] = "Resolved"
                
        incident_log.insert(0, {
            "id": f"INC-{len(incident_log)+101}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "node_id": "ALL",
            "hazard": "System",
            "title": "Network All Clear · Environmental Normalization",
            "severity": "INFO",
            "status": "Resolved",
            "details": "All 4 edge stations returned to nominal safe baseline levels. Actuators reset."
        })

    else:
        return jsonify({"success": False, "error": "Unknown scenario"}), 400

    record_history()
    update_hub_alert_status()
    
    return jsonify({
        "success": True,
        "scenario": scenario,
        "hub": hub_state,
        "nodes": node_states,
        "forecasts": {
            "FLD1": run_gru_forecast("FLD1"),
            "SLD2": run_gru_forecast("SLD2"),
            "FIR3": run_gru_forecast("FIR3"),
            "POL4": run_gru_forecast("POL4")
        }
    })

@app.route("/api/sos", methods=["POST"])
def send_sos():
    """Simulates an automated SIM800L GSM emergency broadcast to NDRF."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    active_threats = [
        f"{n['node_id']} ({n['hazard'].upper()} - {n['location']})" 
        for n in node_states.values() if n["status"] in ["Warning", "Hazardous"]
    ]
    
    sms_payload = {
        "timestamp": now_str,
        "source": "DISASTER-SENTINEL-ORIN-HUB",
        "recipient": "+91-11-24363260 (National Disaster Response Force HQ)",
        "protocol": "GSM AT+CMGS via SIM800L UART1",
        "message": f"CRITICAL DISASTER SOS [{now_str}]: Active emergency triggered at: {', '.join(active_threats) if active_threats else 'Manual Evacuation Alert'}. Deploy response units immediately."
    }
    return jsonify({"success": True, "sms": sms_payload})

def load_web_config():
    config_path = os.path.join(PROJECT_ROOT, "jetson", "config.yaml")
    if os.path.exists(config_path):
        try:
            import yaml
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
                return cfg.get("web_dashboard", {})
        except Exception:
            pass
    return {}

if __name__ == "__main__":
    web_cfg = load_web_config()
    host = web_cfg.get("host", "0.0.0.0")
    port = int(web_cfg.get("port", 5000))
    debug = web_cfg.get("debug", True)

    print("\n=======================================================")
    print("  DISASTER SENTINEL - CENTRAL COMMAND DASHBOARD SERVER")
    print("  NVIDIA Jetson Orin Nano AI Hub | SIH 2026 Qualcomm")
    print("=======================================================")
    print(f"  -> Web Dashboard URL: http://localhost:{port}")
    print(f"  -> LoRa Receiver API: http://localhost:{port}/api/nodes")
    print("=======================================================\n")
    app.run(host=host, port=port, debug=debug)

