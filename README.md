# 🛡️ Disaster Sentinel

> **Solar-Powered Distributed Early-Warning Network with 3-Layer Sensor Confirmation & Edge AI**  
> *Smart India Hackathon (SIH) 2026 · Problem Statement SIH26178 · Qualcomm*

---

## 📌 Project Overview

**Disaster Sentinel** addresses early warning and environmental monitoring in infrastructure-deficient regions.

Instead of relying on basic single-sensor thresholds or cloud dependency, Disaster Sentinel uses **2 solar-powered ESP32 edge nodes** running local TinyML anomaly detection and **3-layer sensor prediction**. Compact LoRa packets are transmitted over long range to a **Jetson Orin Nano** physically located at the Disaster Relief Center. The Jetson performs second-pass 3-layer validation, temporal analysis, and AI hazard prediction locally before triggering emergency alerts via a live FastAPI web dashboard, GSM SMS (SIM800L), buzzer, and strobe warning lights.

---

## 🏗️ System Architecture

```text
                        DISASTER AREA (FIELD)
    ┌─────────────────────────────────────────────────────────┐
    │                                                         │
    │   ┌─────────────────┐       ┌─────────────────────┐     │
    │   │  NODE 1: FLOOD  │       │ NODE 2: FIRE+SLIDE  │     │
    │   │                 │       │                      │     │
    │   │ L1: Water Level │       │ FIRE:                │     │
    │   │ L2: Rain Sensor │       │  L1: Flame/IR        │     │
    │   │ L3: BME280      │       │  L2: MQ-2 Gas/Smoke  │     │
    │   │                 │       │  L3: BME280          │     │
    │   │ ESP32 + TinyML  │       │                      │     │
    │   │ LoRa TX         │       │ LANDSLIDE:           │     │
    │   │ Solar + Battery │       │  L1: MPU6050         │     │
    │   └────────┬────────┘       │  L2: Soil Moisture   │     │
    │            │                │  L3: BME280 (shared) │     │
    │            │                │                      │     │
    │            │                │ ESP32 + TinyML       │     │
    │            │                │ LoRa TX              │     │
    │            │                │ Solar + Battery      │     │
    │            │                └──────────┬───────────┘     │
    │            │                           │                 │
    └────────────┼───────────────────────────┼─────────────────┘
                 │     LoRa 433 MHz          │
                 │     Star Topology         │
                 └───────────┬───────────────┘
                             │
    ═════════════════════════╤═════════════════════════════════
              DISASTER RELIEF CENTER
    ┌────────────────────────┼────────────────────────────────┐
    │                        │                                │
    │                  LoRa RX (SX1278)                       │
    │                        │ SPI                            │
    │                        ▼                                │
    │              ┌──────────────────┐                       │
    │              │ JETSON ORIN NANO │                       │
    │              │                  │                       │
    │              │ Packet Decoder   │                       │
    │              │ 3-Layer Validator│                       │
    │              │ Sensor Fusion    │                       │
    │              │ AI Prediction    │                       │
    │              │ Risk/Severity    │                       │
    │              │ Dashboard Server │                       │
    │              └───────┬──────────┘                       │
    │            ┌─────────┼─────────┐                       │
    │            ▼         ▼         ▼                       │
    │       Dashboard   SIM800L   Buzzer + Strobe            │
    │                      │                                  │
    │                     SMS                                 │
    │                                          [UPS + Mains]  │
    └─────────────────────────────────────────────────────────┘
```

---

## 🎯 3-Layer Sensor Confirmation Matrix

To eliminate false alarms, **every calamity must be confirmed by 3 independent sensor layers**:

| Calamity | Layer 1 (Primary) | Layer 2 (Corroborating) | Layer 3 (Environmental Context) |
|----------|-------------------|--------------------------|---------------------------------|
| 🌊 **FLOOD** | Water Level (Ultrasonic JSN-SR04T) | Rain Sensor (YL-83) | BME280 (Pressure drop + High humidity) |
| 🔥 **FIRE** | Flame/IR Sensor (KY-026) | MQ-2 Gas/Smoke Sensor | BME280 (Temp spike + Humidity drop) |
| ⛰️ **LANDSLIDE** | MPU6050 (Tilt & Vibration) | Capacitive Soil Moisture | BME280 (Rain pressure conditions) |

### 🚦 Confirmation Logic:
- **3 Layers Anomalous + High Combined Score** → 🔴 **RED ALERT** (Dashboard Critical + SMS + Buzzer Continuous + Strobe)
- **2 Layers Anomalous** → 🟠 **ORANGE / 🟡 YELLOW ALERT** (Dashboard Warning + Short Beep)
- **1 Layer Anomalous** → 🟢 **REJECTED AS FALSE ALARM** (e.g. sensor glitch or localized bump)

---

## 🚀 Quick Start Guide

### 1. Jetson Dashboard Server (Simulation Mode)
Run the central orchestrator with simulated field packets (no hardware required):

```bash
cd jetson
python main.py --simulate --port 8080
```
Open dashboard in browser: `http://localhost:8080`

### 2. Run Scenario Simulations
In a separate terminal:
```bash
# Run Flood scenario
python simulation/flood_scenario.py

# Run Fire scenario
python simulation/fire_scenario.py

# Run Landslide scenario
python simulation/landslide_scenario.py

# Run False Alarm Rejection test
python simulation/false_alarm_scenario.py
```

### 3. Flash ESP32 Firmware
Build and upload using PlatformIO:
```bash
# Node 1 (Flood)
cd firmware/node_flood
pio run -t upload

# Node 2 (Fire + Landslide)
cd firmware/node_fire_landslide
pio run -t upload
```

---

## 📂 Repository Structure

```text
.
├── docs/
│   └── disaster-sentinel-project-history.md   # Complete evolution & architectural history
├── firmware/
│   ├── node_flood/                            # ESP32 Node 1 (Flood) firmware
│   └── node_fire_landslide/                   # ESP32 Node 2 (Fire+Landslide) firmware
├── jetson/
│   ├── config.yaml                            # Central Jetson system configuration
│   ├── main.py                                # Master orchestrator
│   ├── receiver/                              # SX1278 SPI driver + Packet Decoder
│   ├── data/                                  # SQLite time-series storage
│   ├── engine/                                # 3-Layer Validator & Risk Predictor
│   ├── alerts/                                # SIM800L SMS + Buzzer/Strobe drivers
│   └── dashboard/                             # FastAPI backend + HTML/CSS/JS frontend
├── ai/
│   ├── tinyml/                                # TinyML baseline anomaly trainer
│   └── jetson_model/                          # Jetson RandomForest hazard predictor
└── simulation/                                # Scenario simulators & fake node generators
```

---

## 🛡️ License & SIH 2026 Credits
Built for **Smart India Hackathon 2026** — Qualcomm Sponsored Problem Statement **SIH26178**.
