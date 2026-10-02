# Disaster Sentinel

> **Solar-Powered Distributed Early-Warning Network with Layered Validation & PyTorch GRU AI Predictive Engine**  
> *Smart India Hackathon (SIH) 2026

---

## Project Overview

**Disaster Sentinel** addresses early warning and environmental monitoring in infrastructure-deficient regions.

Instead of relying on basic single-sensor thresholds or cloud dependency, Disaster Sentinel deploys **4 dedicated solar-powered ESP32 edge nodes** monitoring critical disaster hazards (Flood, Landslide, Fire, Pollution). Compact LoRa packets are transmitted over long range to an **NVIDIA Jetson Orin Nano** gateway located at the Disaster Relief Center. 

The Jetson executes **layered sensor confirmation** and runs a **PyTorch GRU (Gated Recurrent Unit) time-series neural network** to predict future calamity probabilities at **T+15, T+30, and T+60 minutes**. Critical alerts trigger real-time updates on a modern FastAPI Single-Page Application (SPA) web dashboard, as well as redundant emergency alerts via GSM SMS (SIM800L), loud buzzer, and strobe warning lights.

---

## System Architecture

```text
                        DISASTER AREA (FIELD)
    ┌────────────────────────────────────────────────────────────────────────┐
    │                                                                        │
    │  ┌─────────────────┐   ┌──────────────────┐   ┌────────────────────┐   │
    │  │  NODE 1: FLOOD  │   │NODE 2: LANDSLIDE │   │   NODE 3: FIRE     │   │
    │  │   (3-Layer)     │   │    (3-Layer)     │   │    (3-Layer)       │   │
    │  │ L1: BME280      │   │ L1: BME280       │   │ L1: BME280         │   │
    │  │ L2: Rain Gauge  │   │ L2: Soil Moisture│   │ L2: MQ-2 Gas/Smoke │   │
    │  │ L3: Water Level │   │ L3: MPU6050 Tilt │   │ L3: Flame/IR       │   │
    │  │ Node ID: FLD1   │   │ Node ID: SLD2    │   │ Node ID: FIR3      │   │
    │  └────────┬────────┘   └────────┬─────────┘   └─────────┬──────────┘   │
    │           │                 │                       │              │
    │           │      ┌──────────┴───────────────────────┘              │
    │           │      │                                                 │
    │           │      │     ┌─────────────────────┐                     │
    │           │      │     │  NODE 4: POLLUTION  │                     │
    │           │      │     │    (2-Layer Mode)   │                     │
    │           │      │     │ L1: N/A (Bypassed)  │                     │
    │           │      │     │ L2: PM2.5 Dust      │                     │
    │           │      │     │ L3: MQ-135 AQI      │                     │
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

## Photos & Hardware Schematics

Physical prototype photos and hardware layout schematics are stored in the [`photos/`](photos/) directory and highlighted below:

### 1. Circuit & Wiring Layout Schematics

| System Pinout & Wiring Diagram | Multi-Node Circuit Architecture |
|---|---|
| ![System Pinout Diagram](photos/Untitled-layout%20(1).png) | ![Circuit Architecture Schematic](photos/Untitled-layout%20(2).png) |
| *System Pinout & Component Wiring Diagram* | *Multi-Node Circuit & Gateway Connections* |

### 2. Physical Hardware Prototypes & Deployment Showcase

| ESP32 Field Sensor Node Assembly | Jetson LoRa Receiver & Central Gateway |
|---|---|
| ![ESP32 Sensor Node Prototype](photos/WhatsApp%20Image%202026-09-15%20at%2019.50.13.jpeg) | ![LoRa Receiver & Gateway Circuit](photos/WhatsApp%20Image%202026-09-15%20at%2019.50.14.jpeg) |
| *Solar ESP32 Edge Sensor Node Hardware* | *NVIDIA Jetson LoRa Gateway & Receiver Hub* |

| Sensor Integration & Enclosure Wiring | Multi-Node Demonstration Setup |
|---|---|
| ![Sensor Module Integration](photos/WhatsApp%20Image%202026-09-15%20at%2019.50.16.jpeg) | ![Hardware Enclosure & Wiring](photos/WhatsApp%20Image%202026-09-15%20at%2019.50.17.jpeg) |
| *3-Layer Sensor Array Integration* | *Field Enclosure & Power Circuit Wiring* |

### 3. Additional Prototype Photos & Field Shots
- [ESP32 Sensor Breadboard Assembly (Photo 1)](photos/WhatsApp%20Image%202026-09-15%20at%2019.50.13%20(1).jpeg)
- [ESP32 Sensor Breadboard Assembly (Photo 2)](photos/WhatsApp%20Image%202026-09-15%20at%2019.50.13%20(2).jpeg)
- [Sensor Module Array Wiring](photos/WhatsApp%20Image%202026-09-15%20at%2019.50.15.jpeg)
- [Node Sensor Assembly Closeup](photos/WhatsApp%20Image%202026-09-15%20at%2019.50.16%20(1).jpeg)
- [Node Hardware Enclosure (Side View 1)](photos/WhatsApp%20Image%202026-09-15%20at%2019.50.17%20(1).jpeg)
- [Node Hardware Enclosure (Side View 2)](photos/WhatsApp%20Image%202026-09-15%20at%2019.50.17%20(2).jpeg)
- [Power & Battery Charging Circuit](photos/WhatsApp%20Image%202026-09-15%20at%2019.50.18.jpeg)
- [Completed Edge Node Unit](photos/WhatsApp%20Image%202026-09-15%20at%2019.50.19.jpeg)
- [Full SIH Demonstration Network Setup](photos/WhatsApp%20Image%202026-09-15%20at%2019.50.20.jpeg)

---

## Layered Sensor Confirmation Matrix

To eliminate false alarms while supporting specialized node configurations, every disaster is validated across dedicated sensor layers:

| Calamity | Node ID | Validation Mode | Layer 1 (Primary) | Layer 2 (Corroborating) | Layer 3 (Environmental Context) |
|----------|---------|-----------------|-------------------|--------------------------|---------------------------------|
| **FLOOD** | `FLD1` | **3-Layer** | BME280 (Pressure drop + High humidity) | Rain Sensor (YL-83) | Ultrasonic Water Level (HC-SR04) |
| **LANDSLIDE** | `SLD2` | **3-Layer** | BME280 (Pressure & Rain storm context) | Capacitive Soil Moisture | MPU6050 (Tilt & Gyro Vibration) |
| **FIRE** | `FIR3` | **3-Layer** | BME280 (Temp spike + Humidity drop) | MQ-2 Gas/Smoke Sensor | Flame/IR Sensor (KY-026) |
| **POLLUTION** | `POL4` | **2-Layer** | *Bypassed in 2-Layer Mode* | PM2.5 Dust Sensor (GP2Y1010AU0F) | MQ-135 Air Quality Index (AQI) |

### Confirmation Rules:
- **3-Layer Mode (FLD1, SLD2, FIR3)**:
  - **RED ALERT**: All 3 layers anomalous AND combined score >= 0.75 (Triggers Dashboard + SMS + Buzzer + Strobe).
  - **ORANGE / YELLOW**: 1-2 layers anomalous (Warning alert on Dashboard).
  - **GREEN**: Rejects single-layer sensor glitches as false alarms.
- **2-Layer Mode (POL4)**:
  - **RED ALERT**: Both 2 layers anomalous AND combined score >= 0.75.
  - **ORANGE / YELLOW**: 1 layer anomalous AND combined score >= 0.55.

---

## Hardware & Pin Connection Details

Below is the clean, easy-to-read hardware pin mapping for all 4 ESP32 edge nodes and the NVIDIA Jetson Orin Nano central hub. For complete schematic diagrams, power rules, and battery charging circuits, see [hardware_pinout_guide.md](hardware_pinout_guide.md).

### 1. Standard ESP32 SX1278 LoRa Connections (Common to Nodes 1–4)

| SX1278 Pin | ESP32 Pin | Interface / Notes |
|---|---|---|
| SCK | GPIO 18 | SPI Clock |
| MISO | GPIO 19 | SPI Master-In-Slave-Out |
| MOSI | GPIO 23 | SPI Master-Out-Slave-In |
| NSS / CS | GPIO 5 | SPI Chip Select |
| RST | GPIO 14 | Hardware Reset |
| DIO0 | GPIO 2 | Interrupt Request (IRQ) |
| VCC | 3.3V | 3.3V Power Supply Only |
| GND | GND | Shared Ground |

### 2. Field Node Sensor Pinouts

#### Node 1: Flood Monitoring Node (FLD1)
| Component | Component Pin | ESP32 Pin | Function / Description |
|---|---|---|---|
| **HC-SR04 / JSN-SR04T** | TRIG | GPIO 12 | Ultrasonic Trigger Pulse |
| | ECHO | GPIO 13 | Ultrasonic Echo Pulse |
| | VCC / GND | 5V / GND | Power & Ground |
| **YL-83 Rain Sensor** | AO (Analog) | GPIO 34 (ADC1) | Rain Density Reading |
| | DO (Digital) | GPIO 27 | Digital Rain Threshold |
| | VCC / GND | 3.3V / GND | Power & Ground |
| **BME280 Sensor** | SDA / SCL | GPIO 21 / GPIO 22 | I2C Data & Clock (Address: 0x76) |
| | VCC / GND | 3.3V / GND | Power & Ground |
| **Battery Monitor** | ADC Pin | GPIO 36 (ADC1) | 10k/10k Resistor Voltage Divider |

#### Node 2: Landslide Monitoring Node (SLD2)
| Component | Component Pin | ESP32 Pin | Function / Description |
|---|---|---|---|
| **MPU6050 Gyro/Tilt** | SDA / SCL | GPIO 21 / GPIO 22 | Shared I2C Bus (Address: 0x68) |
| | VCC / GND | 3.3V / GND | Power & Ground |
| **Soil Moisture v1.2** | AOUT | GPIO 32 (ADC1) | Soil Water Saturation Level |
| | VCC / GND | 3.3V / GND | Power & Ground |
| **BME280 Sensor** | SDA / SCL | GPIO 21 / GPIO 22 | Shared I2C Bus (Address: 0x76) |
| | VCC / GND | 3.3V / GND | Power & Ground |
| **Battery Monitor** | ADC Pin | GPIO 36 (ADC1) | 10k/10k Resistor Voltage Divider |

#### Node 3: Fire Monitoring Node (FIR3)
| Component | Component Pin | ESP32 Pin | Function / Description |
|---|---|---|---|
| **KY-026 Flame Sensor** | AO / DO | GPIO 34 (ADC1) / GPIO 27 | Infrared Flame Intensity & Digital Output |
| | VCC / GND | 3.3V / GND | Power & Ground |
| **MQ-2 Smoke/Gas** | AO / DO | GPIO 35 (ADC1) / GPIO 26 | Gas Concentration Analog & Digital Output |
| | VCC / GND | 5V / GND | 5V Power Required for Internal Heater |
| **BME280 Sensor** | SDA / SCL | GPIO 21 / GPIO 22 | I2C Data & Clock (Address: 0x76) |
| | VCC / GND | 3.3V / GND | Power & Ground |
| **Battery Monitor** | ADC Pin | GPIO 36 (ADC1) | 10k/10k Resistor Voltage Divider |

#### Node 4: Air Pollution Monitoring Node (POL4 - 2-Layer Mode)
| Component | Component Pin | ESP32 Pin | Function / Description |
|---|---|---|---|
| **MQ-135 Air Quality** | AO / DO | GPIO 34 (ADC1) / GPIO 27 | AQI Analog Reading & Digital Threshold |
| | VCC / GND | 5V / GND | 5V Power Required for Internal Heater |
| **GP2Y1010AU0F Dust** | Pin 3 (LED Drive) | GPIO 12 | Internal IR LED Trigger |
| | Pin 5 (Vo Analog) | GPIO 35 (ADC1) | PM2.5 Dust Voltage Output |
| | Pin 1 / 6 / Pins 2,4 | 5V (resistor) / 5V / GND | Sensor Power & Ground Circuit |
| **Battery Monitor** | ADC Pin | GPIO 36 (ADC1) | 10k/10k Resistor Voltage Divider |

### 3. NVIDIA Jetson Orin Nano Gateway & Alert System

| Connected Device | Device Pin | Jetson 40-Pin Header | Header Pin Number | Function / Notes |
|---|---|---|---|---|
| **SX1278 LoRa Receiver** | MOSI | SPI0_MOSI | Pin 19 | SPI Data Out |
| | MISO | SPI0_MISO | Pin 21 | SPI Data In |
| | SCK | SPI0_SCK | Pin 23 | SPI Clock |
| | CS / NSS | SPI0_CS0 | Pin 24 | SPI Chip Select 0 |
| | RST | GPIO25 | Pin 22 | Hardware Reset |
| | DIO0 | GPIO04 | Pin 7 | Interrupt Request (IRQ) |
| | VCC / GND | 3.3V / GND | Pin 1 / Pin 6 | Power & Common Ground |
| **SIM800L GSM Module** | TXD | UART1_RXD | Pin 10 | Serial Receive |
| | RXD | UART1_TXD | Pin 8 | Serial Transmit |
| | VCC / GND | Ext 4.0V Supply / GND | Ext Power / Pin 6 | Dedicated External Power (2A Peak) |
| **Piezo Alarm Buzzer** | Signal / GND | GPIO18 / GND | Pin 12 / Pin 14 | Transistor Driver Output |
| **Strobe Light Relay** | IN / VCC / GND | GPIO23 / 5V / GND | Pin 16 / Pin 2 / Pin 6 | 5V Relay Trigger for Warning Strobe |

---

## PyTorch GRU AI Prediction Engine

The system features a lightweight Gated Recurrent Unit (GRU) time-series model running locally on the Jetson GPU/CPU:

- **Input**: 30-timestep sliding window of sensor anomaly scores (5 features x 30 for 3-layer nodes; 3 features x 30 for 2-layer POL4).
- **Outputs**: Future disaster probabilities for **T+15 minutes**, **T+30 minutes**, and **T+60 minutes**.
- **Auto-Training**: If model weights (`gru_{hazard}.pt`) are missing at startup, the system automatically generates synthetic scenario data and trains the PyTorch model (~30s) before serving telemetry.

---

## Quick Start Guide

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

## Repository Structure

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
├── photos/                              # Circuit schematics and hardware photos
├── hardware_pinout_guide.md             # Complete hardware pinout & power wiring reference
└── simulation/                          # Fake node generators & scenario runner scripts
```

---

## License & Credits
Built for **Smart India Hackathon 2026** — Qualcomm Sponsored Problem Statement **SIH26178**.

