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




## Project Images

All hardware photos, circuit schematics, dashboard screenshots, and documentation images are stored in the [`project_images/`](project_images/) directory.

---

### [A] System Flowchart

| System Flowchart |
|:---:|
| ![System Flowchart](project_images/Flowchart.jpg) |
| *End-to-end disaster detection and alert flowchart* |

---

### [B] Circuit & Wiring Schematics

| System Pinout & Wiring Diagram | Multi-Node Circuit Architecture |
|:---:|:---:|
| ![Circuit Pinout Schematic](project_images/circuit_pinout_schematic.png) | ![Multi-Node Circuit Architecture](project_images/multi_node_circuit_architecture.png) |
| *System pinout & component wiring diagram* | *Multi-node circuit & gateway connections* |

---

### [C] Dashboard Screenshots

| Dashboard - Main View | Dashboard - Alert Panel |
|:---:|:---:|
| ![Dashboard Main View](project_images/Dashboard00.jpg) | ![Dashboard Alert Panel](project_images/Dashboard01.jpg) |
| *Live sensor telemetry & risk status* | *Active alert & notification panel* |

| Dashboard - Sensor Details | Dashboard - AI Predictions |
|:---:|:---:|
| ![Dashboard Sensor Details](project_images/Dashboard02.jpg) | ![Dashboard AI Predictions](project_images/Dashboard03.jpg) |
| *Individual sensor node data view* | *GRU AI prediction graphs (T+15/30/60m)* |

---

### [D] Hardware Prototypes & Field Deployment

| ESP32 Node Assembly - Photo 1 | ESP32 Node Assembly - Photo 2 |
|:---:|:---:|
| ![ESP32 Node Assembly 01](project_images/esp32_node_assembly_01.jpeg) | ![ESP32 Node Assembly 02](project_images/esp32_node_assembly_02.jpeg) |
| *ESP32 field sensor node assembly (front)* | *ESP32 field sensor node (side view)* |

| ESP32 Node Assembly - Photo 3 | Jetson LoRa Gateway |
|:---:|:---:|
| ![ESP32 Node Assembly 03](project_images/esp32_node_assembly_03.jpeg) | ![Jetson LoRa Gateway](project_images/jetson_lora_gateway_01.jpeg) |
| *ESP32 breadboard wiring detail* | *NVIDIA Jetson LoRa receiver & gateway hub* |

| Sensor Module Wiring | Sensor Integration - Photo 1 |
|:---:|:---:|
| ![Sensor Module Wiring](project_images/sensor_module_wiring_01.jpeg) | ![Sensor Integration 01](project_images/sensor_integration_01.jpeg) |
| *3-layer sensor array wiring layout* | *Sensor module integration on node* |

| Sensor Integration - Photo 2 | Node Enclosure Wiring - Photo 1 |
|:---:|:---:|
| ![Sensor Integration 02](project_images/sensor_integration_02.jpeg) | ![Node Enclosure Wiring 01](project_images/node_enclosure_wiring_01.jpeg) |
| *Sensor module closeup & connections* | *Node field enclosure wiring (view 1)* |

| Node Enclosure Wiring - Photo 2 | Node Enclosure Wiring - Photo 3 |
|:---:|:---:|
| ![Node Enclosure Wiring 02](project_images/node_enclosure_wiring_02.jpeg) | ![Node Enclosure Wiring 03](project_images/node_enclosure_wiring_03.jpeg) |
| *Node field enclosure (view 2)* | *Node field enclosure (view 3)* |

| Node Enclosure Wiring - Photo 4 | Power & Battery Circuit - Photo 1 |
|:---:|:---:|
| ![Node Enclosure Wiring 04](project_images/node_enclosure_wiring_04.jpeg) | ![Power Battery Circuit 01](project_images/power_battery_circuit_01.jpeg) |
| *Node enclosure (view 4)* | *Solar power & battery charging circuit* |

| Power & Battery Circuit - Photo 2 | Completed Edge Node - Photo 1 |
|:---:|:---:|
| ![Power Battery Circuit 02](project_images/power_battery_circuit_02.jpeg) | ![Completed Edge Node 01](project_images/completed_edge_node_01.jpeg) |
| *Battery circuit wiring detail* | *Fully assembled edge sensor node* |

| Completed Edge Node - Photo 2 | Full Demo Network Setup - Photo 1 |
|:---:|:---:|
| ![Completed Edge Node 02](project_images/completed_edge_node_02.jpeg) | ![Full Demo Network Setup 01](project_images/full_demo_network_setup_01.jpeg) |
| *Completed node (side view)* | *Full SIH demonstration network setup* |

| Full Demo Network Setup - Photo 2 | Hardware Overview 1 |
|:---:|:---:|
| ![Full Demo Network Setup 02](project_images/full_demo_network_setup_02.jpeg) | ![Hardware Overview 1](project_images/Hardware00.jpg) |
| *Demo network (alternate view)* | *Hardware component overview* |

| Hardware Overview 2 | Hardware Overview 3 |
|:---:|:---:|
| ![Hardware Overview 2](project_images/Hardware01.jpg) | ![Hardware Overview 3](project_images/Hardware02.jpg) |
| *Hardware assembly detail* | *Node wiring and layout* |

| Hardware Overview 4 | Hardware Overview 5 |
|:---:|:---:|
| ![Hardware Overview 4](project_images/Hardware03.jpg) | ![Hardware Overview 5](project_images/Hardware04.jpg) |
| *Full node circuit view* | *Node deployment ready* |

| Hardware Overview 6 | Hardware Overview 7 |
|:---:|:---:|
| ![Hardware Overview 6](project_images/Hardware05.jpg) | ![Hardware Overview 7](project_images/Hardware06.jpg) |
| *Gateway hardware setup* | *Multi-node layout* |

| Hardware Overview 8 |
|:---:|
| ![Hardware Overview 8](project_images/Hardware07.jpg) |
| *Complete system hardware overview* |

---

### [E] Documentation & Reports

| Documentation Page 1 | Documentation Page 2 |
|:---:|:---:|
| ![Documentation 01](project_images/Documentation00.jpg) | ![Documentation 02](project_images/Documentation01.jpg) |
| *Project documentation (page 1)* | *Project documentation (page 2)* |

| Documentation Page 3 |
|:---:|
| ![Documentation 03](project_images/Documentation02.jpg) |
| *Project documentation (page 3)* |

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
