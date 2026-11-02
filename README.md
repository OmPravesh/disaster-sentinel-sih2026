# Disaster Sentinel

> **Solar-Powered Distributed Early-Warning Network with Layered Sensor Validation and PyTorch GRU AI Predictive Engine**
> Smart India Hackathon (SIH) 2026

---

### Tech Stack

![ESP32](https://img.shields.io/badge/ESP32-Microcontroller-blue?style=flat-square&logo=espressif&logoColor=white)
![C++](https://img.shields.io/badge/C++-Firmware-00599C?style=flat-square&logo=cplusplus&logoColor=white)
![PlatformIO](https://img.shields.io/badge/PlatformIO-Build%20System-orange?style=flat-square&logo=platformio&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-GRU%20AI%20Engine-EE4C2C?style=flat-square&logo=pytorch&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Web%20Dashboard-009688?style=flat-square&logo=fastapi&logoColor=white)
![NVIDIA Jetson](https://img.shields.io/badge/NVIDIA-Jetson%20Orin%20Nano-76B900?style=flat-square&logo=nvidia&logoColor=white)
![LoRa](https://img.shields.io/badge/LoRa-433%20MHz%20Radio-8B4513?style=flat-square)
![GSM](https://img.shields.io/badge/SIM800L-GSM%20SMS%20Alerts-red?style=flat-square)
![Solar Powered](https://img.shields.io/badge/Solar-Powered%20Nodes-FFD700?style=flat-square&logo=sun&logoColor=black)
![SIH 2026](https://img.shields.io/badge/SIH-2026-purple?style=flat-square)

---

## Project Overview

**Disaster Sentinel** is an early-warning and environmental monitoring system built for areas with limited infrastructure.

The system uses **4 solar-powered ESP32 edge sensor nodes**, each dedicated to monitoring a specific disaster type: Flood, Landslide, Fire, and Air Pollution. Each node transmits compact LoRa packets to a central **NVIDIA Jetson Orin Nano** gateway at the Disaster Relief Center.

The Jetson runs **layered sensor confirmation** and a **PyTorch GRU neural network** that predicts disaster probabilities at **T+15, T+30, and T+60 minutes** ahead of time. Alerts are sent in real-time to a web dashboard, and also via GSM SMS, a buzzer, and strobe warning lights.




## Project Gallery & Hardware Showcase

All visual assets, circuit schematics, dashboard telemetry, and hardware photographs are cataloged in [`project_images/`](project_images/).

---

### [A] System Flowchart & Full Hardware Demonstration Setup

| End-to-End System Architecture Flowchart |
|:---:|
| ![System Flowchart](project_images/Flowchart.jpg) |
| *Complete system architecture pipeline: Multi-sensor edge data acquisition, SX1278 LoRa transmission, Jetson Orin Nano edge intelligence (Random Forest + PyTorch GRU), real-time web dashboard, and multi-channel emergency alerting.* |

| Full Hardware Demonstration Setup (Dual-Laptop Command Station & Multi-Node Testbed) |
|:---:|
| ![Full Hardware Setup](project_images/full_hardware_setup.jpg) |
| *End-to-end physical hardware demonstration: Dual-laptop command station running the SIH Technical Approach poster & real-time telemetry dashboard, connected to the NVIDIA Jetson Orin Nano gateway and all 4 ESP32 multi-hazard sensor nodes.* |

| Multi-Node Deployment Array | LoRa Gateway & Field Breadboard Array |
|:---:|:---:|
| ![Multi-Node Array](project_images/full_demo_network_setup_02.jpeg) | ![Node Sensor Bus Wiring](project_images/power_battery_circuit_02.jpeg) |
| *Live 4-node LoRa transmitter array in active operation* | *Sensor bus, voltage regulation, and LoRa antenna integration* |

---

### [B] Circuit Schematics & Network Architecture

| Multi-Node Circuit Architecture | Complete System Pinout & Component Wiring Diagram |
|:---:|:---:|
| ![Multi-Node Circuit Architecture](project_images/multi_node_circuit_architecture.png) | ![Circuit Pinout Schematic](project_images/circuit_pinout_schematic.png) |
| *LoRa star network topology connecting 4 edge nodes to Jetson* | *Full hardware pinout schematic for ESP32 nodes, sensors, and Jetson Orin Nano* |

---

### [C] Dedicated Sensor Nodes & Gateway Hardware (Annotated)

| Node 1: Flood Monitoring (`FLD1`) | Node 1: Ultrasonic Water Level Sensor |
|:---:|:---:|
| ![Flood Monitoring Node](project_images/Hardware03.jpg) | ![Ultrasonic Water Level Sensor](project_images/Hardware02.jpg) |
| *ESP32 Node FLD1: YL-83 Rain Sensor, MPU6050, and LoRa 433MHz* | *Waterproof JSN-SR04T ultrasonic transducer mounted on river gauge pipe* |

| Node 2: Landslide Monitoring (`SLD2`) | Node 2: Inclinometer & Soil Probe Wiring |
|:---:|:---:|
| ![Landslide Monitoring Node](project_images/Hardware05.jpg) | ![Landslide Inclinometer Wiring](project_images/node_enclosure_wiring_03.jpeg) |
| *ESP32 Node SLD2: Capacitive Soil Moisture Sensor & MPU-6050 Tilt* | *Close-up of MPU-6050 tilt accelerometer and soil saturation bus* |

| Node 3: Wildfire Monitoring (`FIR3`) | Node 4: Air Pollution Monitoring (`POL4`) |
|:---:|:---:|
| ![Wildfire Monitoring Node](project_images/Hardware07.jpg) | ![Air Pollution Monitoring Node](project_images/Hardware06.jpg) |
| *ESP32 Node FIR3: KY-026 Flame/IR, BME280, and MQ-2 Gas/Smoke* | *ESP32 Node POL4: MQ-135 AQI, PM2.5 Optical Dust, and LoRa Antenna* |

| NVIDIA Jetson Orin Nano AI Gateway | Jetson SPI LoRa Interface & Cooling |
|:---:|:---:|
| ![Jetson Gateway Hardware](project_images/Hardware04.jpg) | ![Jetson LoRa Gateway Detail](project_images/jetson_lora_gateway_01.jpeg) |
| *Central hub with active fan, SX1278 SPI LoRa receiver, and alert actuators* | *Jetson Orin Nano header pin connections, SPI bus, and status display* |

---

### [D] Edge Node Assembly & Prototype Build

| Microcontroller Core Assembly | Breadboard Prototyping Layout |
|:---:|:---:|
| ![ESP32 Node Assembly 01](project_images/esp32_node_assembly_01.jpeg) | ![ESP32 Node Assembly 02](project_images/esp32_node_assembly_02.jpeg) |
| *ESP32-WROOM-32 microcontroller and pinout header assembly* | *Side perspective of sensor bus wiring and voltage regulation* |

| Sensor Bus Integration | Gateway & Node Cluster Testing |
|:---:|:---:|
| ![ESP32 Sensor Bus Integration](project_images/esp32_node_assembly_03.jpeg) | ![Gateway & Node Cluster Testing](project_images/node_enclosure_wiring_01.jpeg) |
| *Top-down view of breadboard power rails and LoRa SPI connections* | *Integrated bench testing of Jetson gateway and edge sensor clusters* |

---

### [E] Central Command Web Dashboard

| Master Executive Overview | Real-Time Multi-Hazard Telemetry |
|:---:|:---:|
| ![Dashboard Master Overview](project_images/Dashboard03.jpg) | ![Live Monitoring Telemetry](project_images/Dashboard01.jpg) |
| *Master situational awareness: 4 hazard status cards and quick dispatch* | *Dedicated multi-sensor telemetry streams across all 4 edge stations* |

| Geospatial GIS Disaster Map | PyTorch GRU AI Forecasts |
|:---:|:---:|
| ![Geospatial Disaster Map](project_images/Dashboard00.jpg) | ![AI Prediction Trajectory](project_images/Dashboard02.jpg) |
| *Interactive Leaflet satellite mapping with GPS markers and hazard perimeters* | *Recurrent neural network forecasting future trends (T+10m to T+50m)* |

| Live Field Deployment - Overview Screen | Live Field Deployment - GIS Danger Alert Screen |
|:---:|:---:|
| ![Field Test Dashboard](project_images/sensor_integration_01.jpeg) | ![Field Test Map Alert](project_images/sensor_module_wiring_01.jpeg) |
| *Live field validation: Laptop displaying active multi-hazard overview* | *Live field validation: Tactical GIS map displaying active critical alert* |

---

### [F] Technical Posters & Documentation

| SIH Technical Approach (Page 1) | System Architecture & Pipeline (Page 2) |
|:---:|:---:|
| ![Documentation Page 1](project_images/Documentation00.jpg) | ![Documentation Page 2](project_images/Documentation01.jpg) |
| *Problem statement, solution overview, and system features* | *Layered validation architecture and hardware-in-the-loop pipeline* |

| Implementation & Results (Page 3) |
|:---:|
| ![Documentation Page 3](project_images/Documentation02.jpg) |
| *Hardware setup, field validation results, and edge deployment specifications* |

---

## Layered Sensor Confirmation

To eliminate false alarms, every disaster type is validated across multiple dedicated sensor layers:

| Disaster | Node ID | Mode | Layer 1 (Primary) | Layer 2 (Corroborating) | Layer 3 (Context) |
|----------|---------|------|-------------------|--------------------------|--------------------|
| **Flood** | `FLD1` | 3-Layer | BME280 (Pressure drop + High humidity) | Rain Sensor (YL-83) | Ultrasonic Water Level (HC-SR04) |
| **Landslide** | `SLD2` | 3-Layer | BME280 (Pressure & Rain storm context) | Capacitive Soil Moisture | MPU6050 (Tilt & Gyro Vibration) |
| **Fire** | `FIR3` | 3-Layer | BME280 (Temp spike + Humidity drop) | MQ-2 Gas/Smoke Sensor | Flame/IR Sensor (KY-026) |
| **Pollution** | `POL4` | 2-Layer | Bypassed in 2-Layer Mode | PM2.5 Dust Sensor (GP2Y1010AU0F) | MQ-135 Air Quality (AQI) |

### Alert Rules

**3-Layer Nodes (FLD1, SLD2, FIR3):**
- [RED] All 3 layers triggered AND combined score >= 0.75 -> Full alert: Dashboard + SMS + Buzzer + Strobe
- [ORANGE/YELLOW] 1 to 2 layers triggered -> Warning shown on dashboard
- [GREEN] Single-layer trigger only -> Rejected as a false alarm

**2-Layer Node (POL4):**
- [RED] Both layers triggered AND combined score >= 0.75 -> Full alert
- [ORANGE/YELLOW] 1 layer triggered AND combined score >= 0.55 -> Warning

---

## Hardware Pin Connections

A summary of pin connections for all 4 ESP32 nodes and the Jetson gateway. For full schematic diagrams and power wiring, see [hardware_pinout_guide.md](hardware_pinout_guide.md).

### LoRa Module (SX1278) -- Common to All 4 Nodes

| SX1278 Pin | ESP32 Pin | Notes |
|---|---|---|
| SCK | GPIO 18 | SPI Clock |
| MISO | GPIO 19 | SPI Master-In-Slave-Out |
| MOSI | GPIO 23 | SPI Master-Out-Slave-In |
| NSS / CS | GPIO 5 | SPI Chip Select |
| RST | GPIO 14 | Hardware Reset |
| DIO0 | GPIO 2 | Interrupt (IRQ) |
| VCC | 3.3V | 3.3V Power |
| GND | GND | Ground |

### Node 1: Flood Monitoring (FLD1)

| Component | Pin | ESP32 Pin | Function |
|---|---|---|---|
| HC-SR04 Ultrasonic | TRIG / ECHO | GPIO 12 / GPIO 13 | Water level measurement |
| YL-83 Rain Sensor | AO / DO | GPIO 34 / GPIO 27 | Rain density reading |
| BME280 | SDA / SCL | GPIO 21 / GPIO 22 | Temperature, pressure, humidity |
| Battery Monitor | ADC | GPIO 36 | Voltage divider (10k/10k) |

### Node 2: Landslide Monitoring (SLD2)

| Component | Pin | ESP32 Pin | Function |
|---|---|---|---|
| MPU6050 Gyro/Tilt | SDA / SCL | GPIO 21 / GPIO 22 | Ground tilt & vibration |
| Soil Moisture v1.2 | AOUT | GPIO 32 | Soil water saturation |
| BME280 | SDA / SCL | GPIO 21 / GPIO 22 | Temperature, pressure, humidity |
| Battery Monitor | ADC | GPIO 36 | Voltage divider (10k/10k) |

### Node 3: Fire Monitoring (FIR3)

| Component | Pin | ESP32 Pin | Function |
|---|---|---|---|
| KY-026 Flame Sensor | AO / DO | GPIO 34 / GPIO 27 | Infrared flame detection |
| MQ-2 Smoke/Gas | AO / DO | GPIO 35 / GPIO 26 | Gas concentration reading |
| BME280 | SDA / SCL | GPIO 21 / GPIO 22 | Temperature, pressure, humidity |
| Battery Monitor | ADC | GPIO 36 | Voltage divider (10k/10k) |

### Node 4: Air Pollution Monitoring (POL4 -- 2-Layer Mode)

| Component | Pin | ESP32 Pin | Function |
|---|---|---|---|
| MQ-135 Air Quality | AO / DO | GPIO 34 / GPIO 27 | AQI reading |
| GP2Y1010AU0F Dust | LED Drive / Vo | GPIO 12 / GPIO 35 | PM2.5 dust density |
| Battery Monitor | ADC | GPIO 36 | Voltage divider (10k/10k) |

### Jetson Orin Nano -- Gateway & Alert System

| Device | Device Pin | Jetson 40-Pin Header | Pin No. | Notes |
|---|---|---|---|---|
| SX1278 LoRa | MOSI / MISO / SCK / CS | SPI0 pins | 19 / 21 / 23 / 24 | SPI LoRa interface |
| SX1278 LoRa | RST / DIO0 | GPIO25 / GPIO04 | Pin 22 / Pin 7 | Reset & IRQ |
| SIM800L GSM | TXD / RXD | UART1_RXD / TXD | Pin 10 / Pin 8 | SMS alerts |
| Piezo Buzzer | Signal / GND | GPIO18 / GND | Pin 12 / Pin 14 | Audio alarm |
| Strobe Relay | IN | GPIO23 | Pin 16 | 5V relay for warning light |

---

## PyTorch GRU AI Prediction Engine

The system includes a lightweight GRU (Gated Recurrent Unit) time-series model running locally on the Jetson:

- **Input**: 30-timestep sliding window of sensor anomaly scores.
- **Output**: Disaster probability forecasts for **T+15**, **T+30**, and **T+60 minutes**.
- **Auto-Training**: If model weights are missing at startup, the system automatically generates synthetic data and trains the model (~30 seconds) before serving alerts.

---

## Quick Start Guide

### 1. Run the Gateway & Dashboard (Simulation Mode)

No hardware required:

```bash
cd jetson
python main.py --simulate --port 8080
```

Open in browser: `http://localhost:8080`

### 2. Train or Retrain the AI Models

```bash
python ai/jetson_model/train_gru_model.py --epochs 100
```

Model weights are saved to `jetson/data/models/`.

### 3. Run Disaster Scenarios

```bash
# Pollution event (AQI & PM2.5 escalation)
python simulation/pollution_scenario.py

# Flood event
python simulation/flood_scenario.py

# Fire event
python simulation/fire_scenario.py

# Landslide event
python simulation/landslide_scenario.py

# False alarm rejection test
python simulation/false_alarm_scenario.py
```

### 4. Flash ESP32 Firmware

```bash
# Node 1 (Flood - FLD1)
cd firmware/node_flood && pio run -t upload

# Node 2 (Landslide - SLD2)
cd firmware/node_landslide && pio run -t upload

# Node 3 (Fire - FIR3)
cd firmware/node_fire && pio run -t upload

# Node 4 (Pollution - POL4)
cd firmware/node_pollution && pio run -t upload
```

---

## Repository Structure

| Folder / File | What it contains |
|---|---|
| `ai/jetson_model/train_gru_model.py` | PyTorch GRU model trainer for all 4 disaster types |
| `firmware/node_flood/` | ESP32 firmware for Flood node (FLD1) — 3-layer mode |
| `firmware/node_landslide/` | ESP32 firmware for Landslide node (SLD2) — 3-layer mode |
| `firmware/node_fire/` | ESP32 firmware for Fire node (FIR3) — 3-layer mode |
| `firmware/node_pollution/` | ESP32 firmware for Pollution node (POL4) — 2-layer mode |
| `jetson/config.yaml` | Central configuration for all 4 nodes and Jetson settings |
| `jetson/main.py` | Master startup script — launches all services on the Jetson |
| `jetson/receiver/` | SX1278 SPI LoRa packet receiver and binary decoder |
| `jetson/data/models/` | Trained PyTorch GRU model weight files (.pt) |
| `jetson/engine/three_layer_validator.py` | 3-layer and 2-layer sensor confirmation logic |
| `jetson/engine/ai_predictor.py` | PyTorch GRU neural network and prediction manager |
| `jetson/engine/risk_predictor.py` | Risk scoring, severity levels, and ETA calculation |
| `jetson/alerts/` | SMS (SIM800L), buzzer, and strobe light alert drivers |
| `jetson/dashboard/app.py` | FastAPI web server with REST API and WebSocket support |
| `jetson/dashboard/static/` | Frontend CSS and JavaScript for the web dashboard |
| `jetson/dashboard/templates/` | HTML shell for the Single-Page Application |
| `project_images/` | All hardware photos, circuit schematics, and dashboard screenshots |
| `hardware_pinout_guide.md` | Full hardware pin wiring and power circuit reference |
| `simulation/` | Scenario scripts to simulate disaster events for testing |

---

## License

Built for **Smart India Hackathon (SIH) 2026**.
