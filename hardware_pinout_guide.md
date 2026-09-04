# 🔌 Disaster Sentinel — Complete Hardware Pinout & Wiring Guide

> **Beginner-Friendly Hardware & Pin Connection Reference**  
> *SIH 2026 · Problem Statement SIH26178 · Qualcomm*

---

## 📋 Table of Contents
1. [⚡ Critical Wiring Rules for Beginners](#-critical-wiring-rules-for-beginners)
2. [🌊 Node 1: Flood Monitoring Node (FLD1)](#-node-1-flood-monitoring-node-fld1)
3. [⛰️ Node 2: Landslide Monitoring Node (SLD2)](#%EF%B8%8F-node-2-landslide-monitoring-node-sld2)
4. [🔥 Node 3: Fire Monitoring Node (FIR3)](#-node-3-fire-monitoring-node-fir3)
5. [🏭 Node 4: Air Pollution Monitoring Node (POL4 - 2-Layer Mode)](#-node-4-air-pollution-monitoring-node-pol4---2-layer-mode)
6. [🧠 NVIDIA Jetson Orin Nano Central Hub & Alert System](#-nvidia-jetson-orin-nano-central-hub--alert-system)
7. [☀️ Solar Power & Battery Charging Circuit](#%EF%B8%8F-solar-power--battery-charging-circuit)
8. [🔍 SIH Demonstration Wiring Checklist](#-sih-demonstration-wiring-checklist)

---

## ⚡ Critical Wiring Rules for Beginners

Before plugging in any wires, read these 4 golden rules to avoid damaging components:

1. **Common Ground (GND) is Mandatory**:
   - ALL components (ESP32, sensors, relays, power supplies) connected together MUST share a common **GND** wire.
2. **ESP32 3.3V Logic Warning**:
   - ESP32 GPIO pins operate at **3.3V logic level**. Connecting 5V directly to an ESP32 input pin can destroy the chip.
   - For 5V sensors like MQ-2 or MQ-135, power the sensor with 5V, but ensure analog outputs stay below 3.3V (or use a voltage divider).
3. **ADC1 vs ADC2 Pin Rule (ESP32 WiFi/LoRa Compatibility)**:
   - Always use **ADC1 pins** (GPIO 32, 34, 35, 36, 39) for analog sensors when LoRa or WiFi is enabled. **ADC2 pins cannot be used while wireless modules are active!**
4. **SIM800L Power Peak Requirement**:
   - The SIM800L GSM module requires **3.7V – 4.2V** with at least **2 Amps burst current**. Do NOT power SIM800L directly from the Jetson 3.3V/5V pins! Use a dedicated Li-ion battery or LM2596 buck converter.

---

## 🌊 Node 1: Flood Monitoring Node (FLD1)

The Flood Node monitors water accumulation, rainfall, and barometric pressure drops using 3 independent sensor layers.

### 📍 Component Connection Table

| Component Name | Component Pin | Connected to ESP32 Pin | Wire Color Code (Recommended) | Description / Notes |
|---|---|---|---|---|
| **SX1278 LoRa Transceiver** | SCK | **GPIO 18** | 🟢 Green | SPI Clock |
| | MISO | **GPIO 19** | 🟡 Yellow | SPI Master-In-Slave-Out |
| | MOSI | **GPIO 23** | 🟠 Orange | SPI Master-Out-Slave-In |
| | NSS / CS | **GPIO 5** | 🔵 Blue | SPI Chip Select |
| | RST | **GPIO 14** | ⚪ White | Hardware Reset |
| | DIO0 | **GPIO 2** | 🟣 Purple | Interrupt Request (IRQ) |
| | VCC | **3.3V** | 🔴 Red | **3.3V Power ONLY** |
| | GND | **GND** | 🖤 Black | Ground |
| **HC-SR04 / JSN-SR04T** *(Layer 1 Primary)* | TRIG | **GPIO 12** | 🟡 Yellow | Trigger Pulse |
| | ECHO | **GPIO 13** | 🟢 Green | Echo Pulse (3.3V tolerant) |
| | VCC | **5V (VIN)** | 🔴 Red | 5V Power Supply |
| | GND | **GND** | 🖤 Black | Ground |
| **YL-83 Rain Sensor** *(Layer 2 Corroborating)* | AO (Analog) | **GPIO 34** (ADC1_CH6) | 🔵 Blue | Rain Density Analog Reading |
| | DO (Digital) | **GPIO 27** | ⚪ White | Digital Rain Threshold |
| | VCC | **3.3V** | 🔴 Red | 3.3V Power |
| | GND | **GND** | 🖤 Black | Ground |
| **BME280 Sensor** *(Layer 3 Context)* | SDA | **GPIO 21** | 🟢 Green | I2C Data |
| | SCL | **GPIO 22** | 🟡 Yellow | I2C Clock |
| | VCC | **3.3V** | 🔴 Red | 3.3V Power |
| | GND | **GND** | 🖤 Black | Ground (I2C Address: `0x76`) |
| **Battery Divider** | ADC Pin | **GPIO 36** (ADC1_CH0) | 🟣 Purple | Between two 10kΩ resistors (Battery + to GND) |

---

## ⛰️ Node 2: Landslide Monitoring Node (SLD2)

The Landslide Node monitors slope angle, ground tilt, soil moisture saturation, and atmospheric pressure.

### 📍 Component Connection Table

| Component Name | Component Pin | Connected to ESP32 Pin | Wire Color Code | Description / Notes |
|---|---|---|---|---|
| **SX1278 LoRa Transceiver** | SCK | **GPIO 18** | 🟢 Green | SPI Clock |
| | MISO | **GPIO 19** | 🟡 Yellow | SPI Master-In-Slave-Out |
| | MOSI | **GPIO 23** | 🟠 Orange | SPI Master-Out-Slave-In |
| | NSS / CS | **GPIO 5** | 🔵 Blue | SPI Chip Select |
| | RST | **GPIO 14** | ⚪ White | Reset |
| | DIO0 | **GPIO 2** | 🟣 Purple | Interrupt Request (IRQ) |
| | VCC | **3.3V** | 🔴 Red | 3.3V Power |
| | GND | **GND** | 🖤 Black | Ground |
| **MPU6050 Gyro/Tilt** *(Layer 1 Primary)* | SDA | **GPIO 21** | 🟢 Green | I2C Data (Shared bus) |
| | SCL | **GPIO 22** | 🟡 Yellow | I2C Clock (Shared bus) |
| | VCC | **3.3V** | 🔴 Red | 3.3V Power |
| | GND | **GND** | 🖤 Black | Ground (I2C Address: `0x68`) |
| **Soil Moisture v1.2** *(Layer 2 Corroborating)* | AOUT | **GPIO 32** (ADC1_CH4) | 🔵 Blue | Soil Water Saturation Analog |
| | VCC | **3.3V** | 🔴 Red | 3.3V Power |
| | GND | **GND** | 🖤 Black | Ground |
| **BME280 Sensor** *(Layer 3 Context)* | SDA | **GPIO 21** | 🟢 Green | Shared I2C SDA |
| | SCL | **GPIO 22** | 🟡 Yellow | Shared I2C SCL |
| | VCC | **3.3V** | 🔴 Red | 3.3V Power |
| | GND | **GND** | 🖤 Black | Ground (I2C Address: `0x76`) |
| **Battery Divider** | ADC Pin | **GPIO 36** (ADC1_CH0) | 🟣 Purple | Voltage divider (2x 10kΩ) |

---

## 🔥 Node 3: Fire Monitoring Node (FIR3)

The Fire Node detects infrared flame emissions, smoke/combustion gas concentration, and ambient temperature spikes.

### 📍 Component Connection Table

| Component Name | Component Pin | Connected to ESP32 Pin | Wire Color Code | Description / Notes |
|---|---|---|---|---|
| **SX1278 LoRa Transceiver** | SCK | **GPIO 18** | 🟢 Green | SPI Clock |
| | MISO | **GPIO 19** | 🟡 Yellow | SPI MISO |
| | MOSI | **GPIO 23** | 🟠 Orange | SPI MOSI |
| | NSS / CS | **GPIO 5** | 🔵 Blue | SPI CS |
| | RST | **GPIO 14** | ⚪ White | Reset |
| | DIO0 | **GPIO 2** | 🟣 Purple | IRQ |
| | VCC | **3.3V** | 🔴 Red | 3.3V Power |
| | GND | **GND** | 🖤 Black | Ground |
| **KY-026 Flame Sensor** *(Layer 1 Primary)* | AO | **GPIO 34** (ADC1_CH6) | 🔵 Blue | Flame IR Intensity Analog |
| | DO | **GPIO 27** | ⚪ White | Digital Flame Trigger |
| | VCC | **3.3V** | 🔴 Red | 3.3V Power |
| | GND | **GND** | 🖤 Black | Ground |
| **MQ-2 Smoke/Gas Sensor** *(Layer 2 Corroborating)* | AO | **GPIO 35** (ADC1_CH7) | 🔵 Blue | Gas Concentration Analog |
| | DO | **GPIO 26** | ⚪ White | Digital Gas Trigger |
| | VCC | **5V (VIN)** | 🔴 Red | **MUST BE 5V for internal heater!** |
| | GND | **GND** | 🖤 Black | Ground |
| **BME280 Sensor** *(Layer 3 Context)* | SDA | **GPIO 21** | 🟢 Green | I2C Data |
| | SCL | **GPIO 22** | 🟡 Yellow | I2C Clock |
| | VCC | **3.3V** | 🔴 Red | 3.3V Power |
| | GND | **GND** | 🖤 Black | Ground |
| **Battery Divider** | ADC Pin | **GPIO 36** (ADC1_CH0) | 🟣 Purple | Voltage divider (2x 10kΩ) |

---

## 🏭 Node 4: Air Pollution Monitoring Node (POL4 - 2-Layer Mode)

The Pollution Node is a **dedicated 2-layer node** measuring Air Quality Index (AQI) and PM2.5 particulate dust.

### 📍 Component Connection Table

| Component Name | Component Pin | Connected to ESP32 Pin | Wire Color Code | Description / Notes |
|---|---|---|---|---|
| **SX1278 LoRa Transceiver** | SCK | **GPIO 18** | 🟢 Green | SPI Clock |
| | MISO | **GPIO 19** | 🟡 Yellow | SPI MISO |
| | MOSI | **GPIO 23** | 🟠 Orange | SPI MOSI |
| | NSS / CS | **GPIO 5** | 🔵 Blue | SPI CS |
| | RST | **GPIO 14** | ⚪ White | Reset |
| | DIO0 | **GPIO 2** | 🟣 Purple | IRQ |
| | VCC | **3.3V** | 🔴 Red | 3.3V Power |
| | GND | **GND** | 🖤 Black | Ground |
| **MQ-135 Air Quality Sensor** *(Layer 1 Primary)* | AO | **GPIO 34** (ADC1_CH6) | 🔵 Blue | AQI / Gas Analog Reading |
| | DO | **GPIO 27** | ⚪ White | Digital Threshold |
| | VCC | **5V (VIN)** | 🔴 Red | **5V Power for internal heater** |
| | GND | **GND** | 🖤 Black | Ground |
| **GP2Y1010AU0F Dust Sensor** *(Layer 2 Corroborating)* | Pin 3 (LED Drive) | **GPIO 12** | 🟠 Orange | Pulled LOW to drive internal IR LED |
| | Pin 5 (Vo Analog Out) | **GPIO 35** (ADC1_CH7) | 🔵 Blue | PM2.5 Analog Voltage Output |
| | Pin 1 (V-LED) | **5V (via 150Ω resistor)** | 🔴 Red | LED power resistor circuit |
| | Pin 2 & 4 (GND) | **GND** | 🖤 Black | Ground |
| | Pin 6 (VCC) | **5V** | 🔴 Red | 5V Sensor Power |
| **Battery Divider** | ADC Pin | **GPIO 36** (ADC1_CH0) | 🟣 Purple | Voltage divider (2x 10kΩ) |

---

## 🧠 NVIDIA Jetson Orin Nano Central Hub & Alert System

The Jetson Orin Nano receives LoRa telemetry from all 4 field nodes via SPI and controls physical alert devices via GPIO.

### 📍 Jetson 40-Pin Header Connection Table

```text
               JETSON ORIN NANO 40-PIN HEADER TOP-VIEW
                    +3V3 (1)  (2)  +5V
            I2C2_SDA (3)  (4)  +5V
            I2C2_SCL (5)  (6)  GND  <-- Common Ground
    [DIO0]   GPIO04  (7)  (8)  UART1_TX  <-- SIM800L RX
                     GND (9)  (10) UART1_RX  <-- SIM800L TX
    [Buzzer] GPIO18 (11) (12) GPIO18
                     GND (13) (14) GND
    [Strobe] GPIO23 (15) (16) GPIO23
                    +3V3 (17) (18) GPIO24
   [MOSI]  SPI0_MOSI (19) (20) GND
   [MISO]  SPI0_MISO (21) (22) GPIO25   <-- LoRa Reset
   [SCLK]  SPI0_SCK  (23) (24) SPI0_CS0 <-- LoRa CS
```

| Device Name | Device Pin | Connected to Jetson 40-Pin Header | Header Pin Number | Description / Notes |
|---|---|---|---|---|
| **SX1278 LoRa Receiver (SPI0)** | MOSI | SPI0_MOSI | **Pin 19** | SPI Master-Out-Slave-In |
| | MISO | SPI0_MISO | **Pin 21** | SPI Master-In-Slave-Out |
| | SCK | SPI0_SCK | **Pin 23** | SPI Clock |
| | CS / NSS | SPI0_CS0 | **Pin 24** | SPI Chip Select 0 |
| | RST | GPIO25 | **Pin 22** | Hardware Reset |
| | DIO0 | GPIO04 | **Pin 7** | Interrupt Request (IRQ) |
| | VCC | 3.3V | **Pin 1 / 17** | **3.3V Power ONLY** |
| | GND | GND | **Pin 6 / 9 / 14 / 20** | Common Ground |
| **SIM800L GSM Module (UART1)** | TXD | UART1_RXD | **Pin 10** | Jetson receives SMS responses |
| | RXD | UART1_TXD | **Pin 8** | Jetson transmits AT commands |
| | VCC | **External 4.0V Supply** | — | **DO NOT connect to Jetson 5V!** Use 2A power source |
| | GND | GND | **Pin 6 / 14** | Shared GND with Jetson |
| **Active Piezo Alarm Buzzer** | (+) Signal | GPIO18 | **Pin 12** | Via 2N2222 NPN Transistor driver |
| | (-) GND | GND | **Pin 14** | Ground |
| **Strobe Light Relay Module** | IN (Trigger) | GPIO23 | **Pin 16** | Controls 5V relay for high-intensity strobe |
| | VCC | 5V | **Pin 2 / 4** | 5V Relay coil power |
| | GND | GND | **Pin 6 / 14** | Ground |

---

## ☀️ Solar Power & Battery Charging Circuit

Each of the 4 ESP32 field nodes uses an autonomous solar-rechargeable lithium power system.

```text
    ┌────────────────┐
    │ SOLAR PANEL    │
    │ (5V - 6V, 2W)  │
    └───────┬────────┘
            │
            ▼
    ┌────────────────┐       ┌─────────────────┐       ┌─────────────────┐
    │ TP4056 CHARGER │──────►│ 18650 LI-ION    │──────►│ ESP32 NODE      │
    │ MODULE (USB/IN)│       │ BATTERY (3.7V)  │       │ VIN / 3.3V REG  │
    └────────────────┘       └─────────────────┘       └─────────────────┘
            │                                                   │
            └───────────────────────┬───────────────────────────┘
                                    ▼
                             COMMON GND BUS
```

### 📍 Power Wiring Instructions:
1. **Solar Panel (+ / -)** → Connected to `IN+` and `IN-` on the **TP4056 Charger Board**.
2. **18650 Li-ion Battery (+ / -)** → Connected to `B+` and `B-` on the TP4056 board.
3. **TP4056 `OUT+`** → Connected to **ESP32 VIN pin** (or 5V sensor power rail).
4. **TP4056 `OUT-`** → Connected to **ESP32 GND pin**.
5. **Battery Divider Circuit** for voltage monitoring:
   - Connect Battery `B+` → 10kΩ Resistor → **ESP32 GPIO 36** → 10kΩ Resistor → **GND**.

---

## 🔍 SIH Demonstration Wiring Checklist

Before turning on power during your demonstration to the SIH judges, verify:

- [ ] **GND Connected Everywhere**: Every node board has a single continuous ground path.
- [ ] **LoRa Antenna Attached**: **NEVER power on an SX1278 LoRa module without an antenna connected!** Doing so will burn out the RF power amplifier.
- [ ] **MQ-2 / MQ-135 5V Powered**: Gas sensors must be connected to **5V**, not 3.3V, so internal heaters warm up properly.
- [ ] **SIM800L External Battery**: Ensure SIM800L is powered by an external 3.7V–4.2V source with common GND to the Jetson.
- [ ] **BME280 I2C Address**: Confirm BME280 address is `0x76` (or update `config.h` if using `0x77`).
- [ ] **LoRa SPI Pins Correct**: Double-check `SCK=18`, `MISO=19`, `MOSI=23`, `CS=5`, `RST=14`, `DIO0=2` on all ESP32 nodes.

---

*Disaster Sentinel — SIH 2026 · Problem Statement SIH26178 · Qualcomm*
