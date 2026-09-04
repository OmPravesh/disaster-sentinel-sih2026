# 🛡️ Disaster Sentinel

> **Solar-Powered Distributed Early-Warning Network with Layered Validation & PyTorch GRU AI Predictive Engine**  
> *Smart India Hackathon (SIH) 2026 · Problem Statement SIH26178 · Qualcomm*

---

## 📌 Project Overview

**Disaster Sentinel** addresses early warning and environmental monitoring in infrastructure-deficient regions.

Instead of relying on basic single-sensor thresholds or cloud dependency, Disaster Sentinel deploys **4 dedicated solar-powered ESP32 edge nodes** monitoring critical disaster hazards (Flood, Landslide, Fire, Pollution). Compact LoRa packets are transmitted over long range to an **NVIDIA Jetson Orin Nano** gateway located at the Disaster Relief Center. 

The Jetson executes **layered sensor confirmation** and runs a **PyTorch GRU (Gated Recurrent Unit) time-series neural network** to predict future calamity probabilities at **T+15, T+30, and T+60 minutes**. Critical alerts trigger real-time updates on a modern FastAPI Single-Page Application (SPA) web dashboard, as well as redundant emergency alerts via GSM SMS (SIM800L), loud buzzer, and strobe warning lights.

---

## 🏗️ System Architecture

```text
                        DISASTER AREA (FIELD)
    ┌────────────────────────────────────────────────────────────────────────┐
    │                                                                        │
    │  ┌─────────────────┐   ┌──────────────────┐   ┌────────────────────┐   │
    │  │  NODE 1: FLOOD  │   │NODE 2: LANDSLIDE │   │   NODE 3: FIRE     │   │
    │  │   (3-Layer)     │   │    (3-Layer)     │   │    (3-Layer)       │   │
    │  │ L1: Water Level │   │ L1: MPU6050 Tilt │   │ L1: Flame/IR       │   │
    │  │ L2: Rain Gauge  │   │ L2: Soil Moisture│   │ L2: MQ-2 Gas/Smoke │   │
    │  │ L3: BME280      │   │ L3: BME280       │   │ L3: BME280         │   │
    │  │ Node ID: FLD1   │   │ Node ID: SLD2    │   │ Node ID: FIR3      │   │
    │  └────────┬────────┘   └────────┬─────────┘   └─────────┬──────────┘   │
    │           │                 │                       │              │
    │           │      ┌──────────┴───────────────────────┘              │
    │           │      │                                                 │
    │           │      │     ┌─────────────────────┐                     │
    │           │      │     │  NODE 4: POLLUTION  │                     │
    │           │      │     │    (2-Layer Mode)   │                     │
    │           │      │     │ L1: MQ-135 AQI      │                     │
    │           │      │     │ L2: PM2.5 Dust      │                     │
    │           │      │     │ L3: N/A (Bypassed)  │                     │
    │           │      │     │ Node ID: POL4       │                     │
    │           │      │     └──────────┬──────────┘                     │
    │           │      │                │                                │
    └───────────┼──────┼────────────────┼────────────────────────────────┘
                │      │                │
                └──────┴───────┬────────┘   LoRa 433 MHz Star Network
                               │
    ═══════════════════════════╤═══════════════════════════════════════════
               DISASTER RELIEF CENTER (NVIDIA JETSON)
    ┌──────────────────────────┼──────────────────────────────────────────┐
    │                          │                                          │
    │                    LoRa RX (SX1278 SPI)                             │
    │                          │                                          │
    │                          ▼                                          │
    │             ┌──────────────────────────┐                            │
    │             │  NVIDIA JETSON ORIN NANO │                            │
    │             │                          │                            │
    │             │  Packet Decoder & CRC16  │                            │
    │             │  Layered Validator       │                            │
    │             │  PyTorch GRU AI Engine   │ ◄── T+15/30/60m Forecasts │
    │             │  Risk & ETA Calculator   │                            │
    │             │  FastAPI SPA Web Server  │                            │
    │             └────────────┬─────────────┘                            │
    │           ┌──────────────┼──────────────┐                           │
    │           ▼              ▼              ▼                           │
    │      Modern SPA      SIM800L        Buzzer & Strobe                 │
    │      Dashboard      GSM SMS         Warning Lights                  │
    │                                                                     │
    └─────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Layered Sensor Confirmation Matrix

To eliminate false alarms while supporting specialized node configurations, **every disaster is validated across dedicated sensor layers**:

| Calamity | Node ID | Validation Mode | Layer 1 (Primary) | Layer 2 (Corroborating) | Layer 3 (Environmental Context) |
|----------|---------|-----------------|-------------------|--------------------------|---------------------------------|
| 🌊 **FLOOD** | `FLD1` | **3-Layer** | Ultrasonic Water Level (HC-SR04) | Rain Sensor (YL-83) | BME280 (Pressure drop + High humidity) |
| ⛰️ **LANDSLIDE** | `SLD2` | **3-Layer** | MPU6050 (Tilt & Gyro Vibration) | Capacitive Soil Moisture | BME280 (Pressure & Rain storm context) |
| 🔥 **FIRE** | `FIR3` | **3-Layer** | Flame/IR Sensor (KY-026) | MQ-2 Gas/Smoke Sensor | BME280 (Temp spike + Humidity drop) |
| 🏭 **POLLUTION** | `POL4` | **2-Layer** | MQ-135 Air Quality Index (AQI) | PM2.5 Dust Sensor (GP2Y1010AU0F) | ❌ *Bypassed in 2-Layer Mode* |

### 🚦 Confirmation Rules:
- **3-Layer Mode (FLD1, SLD2, FIR3)**:
  - 🔴 **RED ALERT**: All 3 layers anomalous AND combined score ≥ 0.75 (Triggers Dashboard + SMS + Buzzer + Strobe).
  - 🟠 **ORANGE / 🟡 YELLOW**: 1–2 layers anomalous (Warning alert on Dashboard).
  - 🟢 **GREEN**: Rejects single-layer sensor glitches as false alarms.
- **2-Layer Mode (POL4)**:
  - 🔴 **RED ALERT**: Both 2 layers anomalous AND combined score ≥ 0.75.
  - 🟠 **ORANGE / 🟡 YELLOW**: 1 layer anomalous AND combined score ≥ 0.55.

---

## 🤖 PyTorch GRU AI Prediction Engine

The system features a **lightweight Gated Recurrent Unit (GRU) time-series model** running locally on the Jetson GPU/CPU:

- **Input**: 30-timestep sliding window of sensor anomaly scores ($5 \text{ features} \times 30$ for 3-layer nodes; $3 \text{ features} \times 30$ for 2-layer POL4).
- **Outputs**: Future disaster probabilities for **T+15 minutes**, **T+30 minutes**, and **T+60 minutes**.
- **Auto-Training**: If model weights (`gru_{hazard}.pt`) are missing at startup, the system automatically generates synthetic scenario data and trains the PyTorch model (~30s) before serving telemetry.

---

## 🚀 Quick Start Guide

### 1. Jetson Gateway & SPA Dashboard (Simulation Mode)
Run the master orchestrator in simulation mode (no LoRa hardware required):

```bash
cd jetson
python main.py --simulate --port 8080
```
Open the live dashboard in your browser: `http://localhost:8080`

### 2. Train / Retrain PyTorch GRU AI Models
Train the GRU time-series models for all 4 hazard types:

```bash
python ai/jetson_model/train_gru_model.py --epochs 100
```
Trained model weights are exported to `jetson/data/models/`.

### 3. Run Scenario Simulations
Test real-time disaster escalation scenarios in a separate terminal:

```bash
# Run Pollution event scenario (AQI & PM2.5 escalation)
python simulation/pollution_scenario.py

# Run Flood event scenario
python simulation/flood_scenario.py

# Run Fire event scenario
python simulation/fire_scenario.py

# Run Landslide event scenario
python simulation/landslide_scenario.py

# Run False Alarm Rejection test (glitch rejection)
python simulation/false_alarm_scenario.py
```

### 4. Build & Flash ESP32 Firmware
Build and upload node firmware using PlatformIO:

```bash
# Node 1 (Flood — FLD1)
cd firmware/node_flood && pio run -t upload

# Node 2 (Landslide — SLD2)
cd firmware/node_landslide && pio run -t upload

# Node 3 (Fire — FIR3)
cd firmware/node_fire && pio run -t upload

# Node 4 (Pollution — POL4, 2-Layer Mode)
cd firmware/node_pollution && pio run -t upload
```

---

## 📂 Repository Structure

```text
.
├── ai/
│   └── jetson_model/
│       └── train_gru_model.py           # PyTorch GRU model trainer for all 4 hazards
├── firmware/
│   ├── node_flood/                      # ESP32 Node FLD1 (Flood, 3-layer)
│   ├── node_landslide/                  # ESP32 Node SLD2 (Landslide, 3-layer)
│   ├── node_fire/                       # ESP32 Node FIR3 (Fire, 3-layer)
│   └── node_pollution/                  # ESP32 Node POL4 (Pollution, 2-layer mode)
├── jetson/
│   ├── config.yaml                      # Central Jetson 4-node system configuration
│   ├── main.py                          # Master orchestrator & startup manager
│   ├── receiver/                        # SX1278 SPI LoRa receiver & binary decoder
│   ├── data/
│   │   └── models/                      # Trained PyTorch GRU model weights (.pt)
│   ├── engine/
│   │   ├── three_layer_validator.py     # 3-layer & 2-layer validation engine
│   │   ├── ai_predictor.py              # PyTorch GRU neural net & predictor manager
│   │   └── risk_predictor.py            # Risk, severity, ETA & GRU integration
│   ├── alerts/                          # SIM800L SMS, Buzzer, & Strobe light drivers
│   └── dashboard/
│       ├── app.py                       # FastAPI REST API & WebSockets server
│       ├── static/                      # Modern glassmorphism CSS & SPA JavaScript router
│       └── templates/                   # Single-Page Application HTML shell
└── simulation/                          # Fake node generators & scenario runner scripts
```

---

## 🛡️ License & SIH 2026 Credits
Built for **Smart India Hackathon 2026** — Qualcomm Sponsored Problem Statement **SIH26178**.
