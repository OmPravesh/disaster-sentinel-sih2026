# Disaster Sentinel — Complete Project History & Context

> Purpose: This document preserves the complete reasoning, architecture evolution, technical decisions, unresolved questions, problems, corrections, and current direction of the Disaster Sentinel SIH 2026 project.
>
> This file is intended to be given to another LLM, developer, researcher, or team member so they can understand the project without needing to read the entire previous conversation.

---

# 1. Project Identity

## Project Name

**Disaster Sentinel**

## Competition

**Smart India Hackathon (SIH) 2026**

## Problem Statement ID

**SIH26178**

## Sponsor

**Qualcomm**

## General Problem

The project is intended to address disaster monitoring and early warning in infrastructure-deficient or difficult-to-reach regions.

The system is intended to monitor hazards such as:

- Flood
- Landslide
- Fire
- Potentially other environmental hazards through swappable sensor packs

The important architectural insight is that the SIH problem is asking for a **network**, not merely a single sensor connected to a dashboard.

---

# 2. Original Core Idea

The original concept was:

```text
Cheap sensors
        ↓
ESP32
        ↓
LoRa
        ↓
Central system
        ↓
AI
        ↓
Dashboard
        ↓
Alerts
```

The initial goal was to create a low-cost distributed disaster-monitoring system.

The main differentiator proposed was:

```text
Cheap distributed sensors
        ↓
Local observations
        ↓
Multi-node consensus
        ↓
AI-based anomaly/risk analysis
        ↓
Disaster prediction
        ↓
Alerts
```

The intent was to avoid a basic:

```text
Sensor → Threshold → Alert
```

system.

Instead, the project should determine whether multiple observations collectively indicate a real disaster.

---

# 3. Initial Differentiator

The first major differentiator proposed was:

> Cheap sensors cast a wide net (high recall) → neighboring nodes provide corroborating evidence → a consensus mechanism reduces false positives → an escalation model converts raw detections into an actionable risk prediction.

Example:

```text
Node A:
Water level HIGH

Node B:
Water level HIGH

Node C:
Water level HIGH

        ↓

Multi-node consensus

        ↓

Flood probability = 87%

        ↓

Estimated escalation = ~35 minutes

        ↓

Sector B alert
```

The project should therefore focus on:

1. Distributed sensing
2. False-alarm reduction
3. Sensor fusion
4. AI-based risk estimation
5. Early warning
6. Low-cost deployment
7. Operation in infrastructure-deficient areas

---

# 4. Existing Team Advantage

The team already has experience deploying **YOLOv8 on Jetson** for an elephant-detection project.

The existing ONNX/TensorRT deployment experience was considered a genuine advantage.

The original idea was to reuse that experience for visual disaster confirmation.

However, this later changed.

---

# 5. Initial Jetson + YOLO Idea

The original architecture considered:

```text
Sensor nodes
      ↓
LoRa
      ↓
Jetson
      ↓
Sensor AI
      +
YOLO camera
      ↓
Final decision
      ↓
Dashboard / SMS
```

The camera would provide visual confirmation.

For example:

```text
Sensors:
Flood probability = 92%

Camera:
Flooded road detected

        ↓

Combined confidence

        ↓

HIGH CONFIDENCE FLOOD
```

The idea was to use computer vision to reduce false alarms.

---

# 6. Problem: Raspberry Pi vs Jetson

An earlier design considered using a Raspberry Pi as the central gateway.

This was rejected.

## Final decision

Use:

**Jetson Orin Nano**

instead of Raspberry Pi.

Reasons:

* Existing team experience
* GPU acceleration
* Suitable for AI inference
* ONNX/TensorRT experience
* Ability to run multiple AI/data-processing services
* Can host the dashboard backend
* Can process multiple sensor streams
* Can handle more computationally demanding models

The Jetson should become the central intelligence platform.

---

# 7. Problem: ESP32 Role Was Initially Ambiguous

There were two different possible ESP32 architectures.

## Architecture A

ESP32 only senses and transmits.

```text
Sensor
 ↓
ESP32
 ↓
LoRa
```

## Architecture B

ESP32 performs TinyML.

```text
Sensor
 ↓
ESP32
 ↓
TinyML
 ↓
LoRa
```

The architecture initially leaned toward the simpler:

```text
ESP32 = Sense + Transmit
Jetson = Intelligence
```

because the goal was to keep the field nodes extremely cheap.

---

# 8. Revised ESP32 + TinyML Concept

Later, a more sophisticated architecture was proposed:

```text
Sensor
 ↓
ESP32
 ↓
TinyML / anomaly detection
 ↓
LoRa
 ↓
Jetson
 ↓
Network-level AI
```

This creates two levels of intelligence.

## Level 1 — ESP32

The ESP32 answers:

> "Is the environment around this node behaving unusually?"

## Level 2 — Jetson

The Jetson answers:

> "Does the combined evidence from multiple nodes indicate a real disaster?"

This is now considered a potentially stronger architecture.

---

# 9. Important Correction: TinyML Should Not Be Trained From Scratch Using Only 48–78 Hours

A major issue was identified around the idea of training TinyML using approximately 48–78 hours of environmental data.

A model trained only on 48–78 hours of normal environmental data cannot reliably learn the complete concept of:

```text
Flood
Landslide
Fire
```

unless appropriate labeled disaster/non-disaster data already exists.

Therefore the 48–78 hour period should primarily be used for:

**Local environmental baseline establishment.**

Example:

```text
First 48–78 hours
        ↓
Collect normal readings
        ↓
Learn local baseline
        ↓
Normal water level
Normal rain
Normal temperature
Normal soil moisture
Normal vibration
        ↓
Future measurements
        ↓
Detect deviation
        ↓
Anomaly score
```

The ESP32 can therefore perform **anomaly detection**, rather than pretending that it learned a complete disaster classifier from only a few days of data.

---

# 10. Recommended TinyML Role

The ESP32 should preferably calculate something like:

```text
anomaly_score = 0.87
```

rather than:

```text
FLOOD = TRUE
```

The packet sent to Jetson can contain:

```text
NODE=F01
WATER=69
RAIN=35
TEMP=29
ANOMALY=0.87
BATTERY=91
```

The Jetson then performs the more complex interpretation.

---

# 11. Problem: Threshold-Only Detection Is Too Weak

A basic system would do:

```text
IF water_level > 70 cm:
    flood = TRUE
```

This is insufficient.

Example:

```text
Water:
69 → 69 → 69 → 69
```

is very different from:

```text
Water:
50 → 55 → 60 → 65 → 69
```

The second case has a dangerous rate of increase even though the absolute value has not crossed the threshold.

Therefore the system should consider:

* Current value
* Historical baseline
* Rate of change
* Anomaly score
* Neighboring nodes
* Spatial correlation
* Temporal correlation
* Hazard-specific relationships

---

# 12. Proposed Two-Level Decision System

## Field level

```text
Sensors
 ↓
ESP32
 ↓
TinyML anomaly detection
 ↓
Anomaly score
 ↓
LoRa
```

## Central level

```text
LoRa Receiver
 ↓
Jetson
 ↓
Collect data from multiple nodes
 ↓
Sensor fusion
 ↓
Consensus
 ↓
AI prediction
 ↓
Risk probability
 ↓
Alert
```

---

# 13. Jetson's Responsibilities

The Jetson Orin Nano is the central brain.

It should perform:

1. LoRa packet reception
2. Packet decoding
3. Node identification
4. Data validation
5. Data storage
6. Time-series processing
7. Multi-node sensor fusion
8. Consensus analysis
9. Anomaly analysis
10. Hazard classification
11. Risk probability estimation
12. Severity estimation
13. Potential escalation/ETA estimation
14. Dashboard backend
15. Alert decision
16. SMS triggering
17. Local alarm triggering

---

# 14. Final Jetson Architecture

```text
                  JETSON ORIN NANO
                 ==================

LoRa packets
     ↓
Packet receiver
     ↓
Packet decoder
     ↓
Node database
     ↓
Time-series data
     ↓
┌─────────────────────────────┐
│ Multi-node sensor fusion    │
└──────────────┬──────────────┘
               ↓
        Consensus engine
               ↓
        Anomaly analysis
               ↓
       Hazard AI model
               ↓
        Risk probability
               ↓
        Severity + ETA
               ↓
       Alert decision
          ┌────┼────┐
          ↓    ↓    ↓
      Dashboard SMS Buzzer
```

---

# 15. Problem: Camera / YOLO Was Later Removed

The initial design considered a camera and YOLO.

However, the user later explicitly decided:

> Do not use a camera for this project.

Therefore:

## Current architecture

**NO CAMERA**

**NO YOLO**

The Jetson's AI responsibility is now focused on sensor data and multi-node fusion.

This makes the system simpler and keeps the project focused on distributed environmental sensing.

The existing YOLOv8 experience can still be mentioned as team background, but it should NOT be part of the core hardware architecture unless the team later changes the decision.

---

# 16. Final Deployment Location of Jetson

Another major clarification was made.

The Jetson should **NOT** be deployed in the disaster field.

Instead:

```text
Disaster area
    ↓
Distributed ESP32 nodes
    ↓
LoRa
    ↓
Disaster Relief Center
    ↓
LoRa Receiver
    ↓
Jetson Orin Nano
```

The Jetson is physically located inside the:

**Disaster Relief Center / Command Center**

Advantages:

* Protects expensive hardware
* Provides stable power
* Allows operators to access the dashboard
* Allows local alarms
* Provides a central AI decision point
* Makes maintenance easier
* Allows GSM/network connectivity
* Field nodes remain cheap and autonomous

---

# 17. Final Communication Architecture

The final communication chain is:

```text
FIELD SENSOR
     ↓
ESP32
     ↓
LoRa transmitter
     ↓
Wireless LoRa communication
     ↓
LoRa receiver
     ↓
Jetson Orin Nano
```

There should be **no ESP32 gateway at the relief center** in the final design.

The LoRa receiver connects directly to the Jetson.

---

# 18. UPDATED: Two ESP32 Nodes

The system uses **2 ESP32 field nodes** (changed from original 4-node design).

```text
Node 1: FLOOD
Node 2: FIRE + LANDSLIDE (combined)
```

Each node uses a **3-layer sensor prediction** system for calamity confirmation.

---

# 19. 3-Layer Sensor Prediction System

For every calamity, three independent sensor layers must agree before confirmation:

### Layer 1 — Primary Sensor (Direct measurement)
### Layer 2 — Corroborating Sensor (Related environmental measurement)
### Layer 3 — Environmental Context Sensor (Broader environmental validation)

All three layers must show anomalous readings for a calamity to be confirmed.

This is designed to satisfy judges that a real calamity is occurring, not a sensor malfunction.

---

# 20. Recommended Node Architecture

## Node 1 — Flood

### Layer 1: Water Level Sensor (direct flood indicator)
### Layer 2: Rain Sensor (corroborating — flooding correlates with heavy rain)
### Layer 3: BME280 Temperature/Humidity/Pressure (environmental context — storm conditions)

## Node 2 — Fire + Landslide (combined)

### Fire Detection:
- Layer 1: Flame/IR Sensor (direct fire indicator)
- Layer 2: MQ-series Gas Sensor (smoke/CO detection — corroborating)
- Layer 3: BME280 Temperature/Humidity (environmental context — temperature spike, humidity drop)

### Landslide Detection:
- Layer 1: MPU6050 Accelerometer/Gyroscope (direct ground movement)
- Layer 2: Soil Moisture Sensor (corroborating — saturated soil triggers slides)
- Layer 3: BME280 Temperature/Humidity/Pressure (environmental context — rain/pressure changes)

---

# 21. Field Power Architecture

Each field node should be solar-powered.

The architecture:

```text
Solar Panel
     ↓
Solar Charge Controller
     ↓
Rechargeable Battery
     ↓
Voltage Regulator
     ↓
ESP32 + Sensors + LoRa
```

---

# 22. Alert System

Three-layer alert:

```text
                 Jetson
                    │
          ┌─────────┼─────────┐
          ↓         ↓         ↓
      Dashboard    GSM      Local Alarm
                   │
                SIM800L
                   │
                   ↓
                  SMS
```

---

# 23. Current Project Philosophy

1. **Cheap at the edge**
2. **Intelligent at the center**
3. **Low-bandwidth communication**
4. **Solar-powered field nodes**
5. **Local processing**
6. **No mandatory cloud dependency**
7. **3-layer sensor confirmation for every calamity**
8. **Consensus instead of single-threshold decisions**
9. **Prediction instead of only detection**
10. **Multiple emergency alert channels**
11. **Modular hazard-specific sensor packs**
12. **Scalable architecture**

---

# END OF DISASTER SENTINEL PROJECT HISTORY
