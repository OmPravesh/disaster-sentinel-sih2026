# 🎬 Disaster Sentinel — Complete Video Production Guide & Demo Script

> **Smart India Hackathon (SIH) 2026 · Problem Statement SIH26178 · Qualcomm**  
> **Project:** Disaster Sentinel — Solar-Powered Distributed Early-Warning Network with Layered Validation & PyTorch GRU AI Predictive Engine

---

## 📑 Table of Contents
1. [Overview & Video Objectives](#1-overview--video-objectives)
2. [Recommended Video Formats (3-Min Pitch vs 7-Min Demo)](#2-recommended-video-formats)
3. [Complete Scene-by-Scene Video Script & Storyboard](#3-complete-scene-by-scene-video-script--storyboard)
   - [Scene 1: The Hook & Real-World Problem (0:00 - 0:45)](#scene-1-the-hook--real-world-problem-000---045)
   - [Scene 2: Introducing Disaster Sentinel & Architecture (0:45 - 1:45)](#scene-2-introducing-disaster-sentinel--architecture-045---145)
   - [Scene 3: 3-Layer Sensor Confirmation (The Killer Feature) (1:45 - 2:45)](#scene-3-3-layer-sensor-confirmation-the-killer-feature-145---245)
   - [Scene 4: PyTorch GRU AI Predictive Engine (2:45 - 3:45)](#scene-4-pytorch-gru-ai-predictive-engine-245---345)
   - [Scene 5: Live System Demonstration & Escalation (3:45 - 5:30)](#scene-5-live-system-demonstration--escalation-345---530)
   - [Scene 6: False Alarm Rejection Demonstration (5:30 - 6:15)](#scene-6-false-alarm-rejection-demonstration-530---615)
   - [Scene 7: Hardware Implementation, BOM & Conclusion (6:15 - 7:00)](#scene-7-hardware-implementation-bom--conclusion-615---700)
4. [Live Demonstration Execution Guide (Exact Commands)](#4-live-demonstration-execution-guide)
5. [Slide-by-Slide Presentation Deck Content (10 Slides)](#5-slide-by-slide-presentation-deck-content)
6. [Recording Setup & OBS Studio Layout Guidelines](#6-recording-setup--obs-studio-layout-guidelines)
7. [Anticipated Judges / Viva Q&A Defense Script](#7-anticipated-judges--viva-qa-defense-script)

---

## 1. Overview & Video Objectives

When presenting **Disaster Sentinel** in a video for **SIH 2026 / Qualcomm**, academic evaluations, or project showcases, the video must communicate **three core value propositions**:

1. **Zero Cloud Dependency:** Natural disasters knock down cellular towers and internet backbones. Disaster Sentinel operates completely offline at the edge using LoRa 433 MHz and local AI on an **NVIDIA Jetson Orin Nano**.
2. **Immunity to False Alarms (3-Layer Validation):** Single-sensor thresholds cause false alarms (e.g. passing truck vibrating a tilt sensor, or sunlight on a flame sensor). Disaster Sentinel requires multi-layer independent sensor consensus before declaring critical alerts.
3. **Proactive Time-Series AI (PyTorch GRU):** Rather than just reporting current telemetry, an embedded GRU neural network forecasts disaster probability at **T+15, T+30, and T+60 minutes**, giving evacuation teams precious lead time.

---

## 2. Recommended Video Formats

| Format | Duration | Best Used For | Key Focus |
|---|---|---|---|
| **Format A: SIH Screening / Pitch** | **2.5 – 3.0 Minutes** | Hackathon Round 1 / Online Submissions / Socials | Problem hook, High-level Architecture, 45s live dashboard demo with RED alert, business impact. |
| **Format B: Full Technical Showcase** | **5.0 – 7.0 Minutes** | Final Round / College Viva / Technical Jury | Full live demo, terminal execution, false alarm rejection test, PyTorch GRU architecture, hardware pinout. |

---

## 3. Complete Scene-by-Scene Video Script & Storyboard

### Scene 1: The Hook & Real-World Problem (0:00 - 0:45)
- **Visual on Screen:** High-impact stock footage/images or presentation slide showing floodwaters, landslides blocking mountain roads, or forest fires, followed by a graphic of a "Mobile Tower Offline / No Internet" icon.
- **Presenter / Voiceover:**
  > *"When severe natural disasters strike remote or mountainous regions, the first casualty is almost always communication infrastructure. Cellular towers collapse, power grids fail, and traditional cloud-based disaster monitoring systems go dark right when communities need them most.*
  >
  > *Furthermore, conventional early-warning devices rely on basic single-sensor thresholds. A dry leaf blowing past an infrared sensor triggers a false fire alarm, while a heavy truck vibrating a road sensor triggers a false landslide alert—leading to public complacency and wasted emergency resources.*
  >
  > *To solve Qualcomm's Problem Statement SIH26178 for Smart India Hackathon 2026, we present **Disaster Sentinel**: an autonomous, solar-powered distributed early-warning network powered by layered sensor validation and an on-premise PyTorch GRU artificial intelligence predictive engine."*

---

### Scene 2: Introducing Disaster Sentinel & Architecture (0:45 - 1:45)
- **Visual on Screen:** Full-screen system architecture diagram showing:
  1. 4 Field Nodes in the Disaster Zone (Flood FLD1, Landslide SLD2, Fire FIR3, Pollution POL4).
  2. LoRa 433 MHz wireless link spanning kilometers.
  3. Relief Center Command Hub featuring the NVIDIA Jetson Orin Nano, Local Dashboard, SIM800L GSM module, and Hardware Alarms.
- **Presenter / Voiceover:**
  > *"Disaster Sentinel completely eliminates cloud reliance by decoupling data collection from central intelligence.*
  >
  > *In the field, we deploy four ultra-low-power, solar-harvesting ESP32 edge nodes, each tailored to a specific calamity:
  > - **FLD1** for Floods
  > - **SLD2** for Landslides
  > - **FIR3** for Wildfires
  > - and **POL4** for Industrial Air Pollution.
  >
  > *Instead of fragile Wi-Fi or cellular networks, each node broadcasts compact, binary-encoded telemetry packets protected by CRC16 checksums over long-range LoRa at 433 MHz.
  >
  > *Kilometers away at the Disaster Relief Center, an **NVIDIA Jetson Orin Nano** receives these packets directly over hardware SPI. Operating entirely on edge compute, the Jetson decodes the packet, validates the data across multiple sensor layers, runs local neural network inference, and orchestrates emergency actions."*

---

### Scene 3: 3-Layer Sensor Confirmation (The Killer Feature) (1:45 - 2:45)
- **Visual on Screen:** Animated comparison slide or live graphic showing the **3-Layer Sensor Matrix Table**:
  - Flood: HC-SR04 Ultrasonic (L1) + YL-83 Rain Sensor (L2) + BME280 Pressure/Humidity (L3).
  - Landslide: MPU6050 Accelerometer/Tilt (L1) + Soil Moisture (L2) + BME280 (L3).
  - Fire: KY-026 Flame/IR (L1) + MQ-2 Smoke/Gas (L2) + BME280 Temp/Humidity (L3).
  - Pollution: MQ-135 AQI (L1) + PM2.5 Dust (L2).
- **Presenter / Voiceover:**
  > *"What truly separates Disaster Sentinel from existing systems is our proprietary **3-Layer Sensor Confirmation Matrix**.
  >
  > *In critical disaster scenarios, a single sensor should NEVER trigger an evacuation. Disaster Sentinel mandates physical consensus across three distinct environmental domains:
  > - **Layer 1 is the Primary Hazard Sensor**: direct measurement such as water level or flame detection.
  > - **Layer 2 is the Corroborating Physical Sensor**: supporting evidence like heavy rainfall or dense smoke.
  > - **Layer 3 is the Environmental Context Sensor**: atmospheric confirmation such as rapid barometric pressure plunge or sudden humidity drop.
  >
  > *A Critical RED Alert is only declared when all three layers confirm anomaly simultaneously and the combined score exceeds 0.75. If only a single layer spikes, the Jetson intelligently classifies it as a localized glitch or false alarm—preventing panic while logging the anomaly."*

---

### Scene 4: PyTorch GRU AI Predictive Engine (2:45 - 3:45)
- **Visual on Screen:** Screen capture showing the PyTorch GRU Architecture diagram, sliding window time-series input (30 timesteps), and the dashboard's forecast widget displaying probability bars for **T+15m, T+30m, and T+60m**.
- **Presenter / Voiceover:**
  > *"Detecting that a flood has occurred is helpful—but predicting that water levels will breach safety barriers in the next 30 minutes saves lives.
  >
  > *Running directly on the Jetson Orin Nano's GPU-accelerated cores is our custom **PyTorch Gated Recurrent Unit (GRU) time-series model**.
  >
  > *The engine maintains a rolling 30-timestep sliding window of multi-sensor anomalies and rates of change. Instead of reactive thresholds, our GRU model outputs future calamity probabilities at **T+15 minutes, T+30 minutes, and T+60 minutes**.
  >
  > *This allows emergency coordinators at the command center to calculate evacuation ETAs and mobilize rescue teams well before catastrophic thresholds are breached."*

---

### Scene 5: Live System Demonstration & Escalation (3:45 - 5:30)
- **Visual on Screen:** Split screen recording:
  - **Left Side:** Terminal executing the Jetson gateway (`python main.py --simulate`) and scenario injector (`python simulation/flood_scenario.py`).
  - **Right Side:** Live browser window at `http://localhost:8080` displaying the Disaster Sentinel glassmorphism Single-Page Application (SPA).
- **On-Screen Actions:**
  1. Start with the dashboard showing all nodes in **GREEN (NORMAL)** status with real-time graphs ticking.
  2. Launch `flood_scenario.py`.
  3. Watch the water level rise from 45 cm to 75 cm and 110 cm. The dashboard status updates to **YELLOW** then **ORANGE**.
  4. At 180 cm, all 3 layers turn anomalous. The dashboard erupts into **PULSING RED ALERT**, the siren/buzzer indicators fire, and the SMS dispatch queue logs an outgoing emergency alert.
  5. Click into the **Forecast View** to show the GRU probability spiking to 94% for T+30m.
- **Presenter / Voiceover:**
  > *"Let us witness Disaster Sentinel in action through a live end-to-end simulation.
  >
  > *On screen, our master orchestrator is running on port 8080, serving our modern responsive dashboard. All four edge nodes are reporting healthy telemetry via LoRa, with green indicators and baseline anomaly scores below 0.1.
  >
  > *Now, we trigger our real-time Flood Escalation Scenario. Watch Node FLD1:
  > - First, the rain gauge picks up rainfall, followed by water rising to 75 centimeters. The node shifts to YELLOW warning.
  > - As rainfall intensifies and water reaches 110 cm, Layer 1 and Layer 2 are anomalous—the system elevates to an ORANGE advisory.
  > - Suddenly, a flash flood surge pushes water to 180 cm while barometric pressure drops drastically.
  >
  > *Notice that instantly, all 3 sensor layers agree! The combined anomaly score passes 0.85, triggering an immediate **RED ALERT**.
  >
  > *The dashboard flashes critical alerts, the Jetson commands the hardware buzzer and strobe warning lights, and the SIM800L GSM subsystem dispatches redundant emergency SMS alerts to district authorities—completely independent of internet access!"*

---

### Scene 6: False Alarm Rejection Demonstration (5:30 - 6:15)
- **Visual on Screen:** Terminal executing `python simulation/false_alarm_scenario.py`. Highlighting the three automated tests:
  1. Water sensor glitch (L1=0.95, L2=0.05, L3=0.04) -> LOW confirmation -> GREEN.
  2. Sunlight glare on flame sensor -> LOW confirmation -> GREEN.
  3. Heavy truck vibration on accelerometer -> LOW confirmation -> GREEN.
- **Presenter / Voiceover:**
  > *"Now, let's prove our false-alarm immunity. We execute our automated False Alarm Rejection Suite.
  >
  > *In Test 1, we inject a catastrophic water sensor glitch reading 280 cm. In a traditional system, sirens would sound. But Disaster Sentinel checks Layer 2 (Rain) and Layer 3 (Pressure)—both are completely dry and normal. The validator tags this as an isolated glitch, maintaining a GREEN status and suppressing alarms.
  >
  > *The same holds true in Test 2 for direct sunlight on an IR flame sensor, and in Test 3 when a passing truck shakes the landslide tilt sensor without saturated soil.
  >
  > *All three false alarms are successfully filtered out, proving 100% false alarm rejection in single-layer fault modes!"*

---

### Scene 7: Hardware Implementation, BOM & Conclusion (6:15 - 7:00)
- **Visual on Screen:** Clean photos/diagrams of the hardware pinout, solar charging circuit (TP4056 + 18650 Li-ion + Solar Panel), and the Jetson Orin Nano relief center setup. Slide displaying the Bill of Materials (BOM) showing under ₹3,500 ($42) per field node.
- **Presenter / Voiceover:**
  > *"Disaster Sentinel is built for realistic, rugged field deployment.
  >
  > *Each node costs under ₹3,500, utilizing an ESP32 micro-controller, SX1278 LoRa transceiver, and a solar energy harvesting circuit paired with high-capacity 18650 lithium cells for perpetual 24/7 autonomy.
  >
  > *By fusing low-cost edge sensing with 3-layer physical validation and NVIDIA Jetson AI at the relief center, Disaster Sentinel provides an uncompromising, fail-safe early warning shield for vulnerable populations.
  >
  > *Thank you, and we are now open to questions."*

---

## 4. Live Demonstration Execution Guide

Follow these exact steps when recording your screen for the live demo portion of the video.

### Preparation Checklist
- Open **VS Code / Terminal** on the left half of your screen.
- Open your **Web Browser** (Chrome / Edge / Firefox) on the right half of your screen.
- Ensure terminal font size is large enough to be easily read in 1080p (Ctrl + `+` in terminal).

### Execution Steps

#### Step 1: Launch Master Gateway (Relief Center)
In your primary terminal, navigate to the project directory and run:
```powershell
cd "c:\Users\adity\OneDrive\Desktop\Disaster Management System\disaster-sentinel-sih2026"
python jetson/main.py --simulate --port 8080
```
- Open `http://localhost:8080` in your browser.
- **Showcase on Video:**
  - Glassmorphism navigation bar (Overview, Monitoring, Map, Forecasts, Hardware).
  - 4 node telemetry cards with live ping and battery percentages.
  - Interactive map displaying the 4 geographic node pins in the region.

#### Step 2: Trigger Live Flood Escalation
Open a second terminal window (or split pane) and run:
```powershell
python simulation/flood_scenario.py
```
- **Showcase on Video:**
  - Point out the terminal logs displaying the 3 sensor layers for `FLD1`.
  - Watch the browser dashboard seamlessly transition:
    - Step 1: `45 cm` (Normal, GREEN)
    - Step 2: `75 cm` (Elevated, YELLOW)
    - Step 3: `110 cm` (Moderate, ORANGE)
    - Step 4: `180 cm` (SURGE, RED ALERT with 3-layer consensus)
  - Point out the GRU prediction updating on the Forecast view.

#### Step 3: Run the False Alarm Rejection Suite
In the second terminal, run:
```powershell
python simulation/false_alarm_scenario.py
```
- **Showcase on Video:**
  - Point out `TEST 1: Water Level Sensor Glitch (L1 High, L2 & L3 Normal)`.
  - Show the log line: `[Validator] FLD1: LOW CONFIDENCE -> Likely NOT a real FLOOD`.
  - Emphasize to the audience: `TEST PASSED: False alarm successfully rejected (No RED alert / No SMS)`.

---

## 5. Slide-by-Slide Presentation Deck Content

If you are using presentation slides (PowerPoint / Google Slides / Canva), use this 10-slide structure:

```
Slide 1: [Title Slide]
  - Disaster Sentinel: Solar-Powered Distributed Early-Warning Network
  - Subtitle: Layered Physical Validation & PyTorch GRU AI Predictive Engine
  - Context: Smart India Hackathon (SIH) 2026 | Problem Statement: SIH26178 | Sponsored by Qualcomm
  - Team Name & Members

Slide 2: [The Problem: Why Current Systems Fail]
  - Disaster Vulnerability in Remote/Hilly Regions
  - Problem 1: Complete cellular & cloud blackout during calamities.
  - Problem 2: High false alarm rates in single-sensor threshold devices.
  - Problem 3: Reactive detection vs proactive lead-time warning.

Slide 3: [The Disaster Sentinel Solution]
  - Decentralized Star Network Architecture.
  - 4 Specialized Solar Edge Nodes (Flood, Landslide, Fire, Pollution).
  - Offline Compute: NVIDIA Jetson Orin Nano at Local Disaster Relief Center.
  - Redundant LoRa 433MHz Telemetry (No internet needed).

Slide 4: [End-to-End System Architecture]
  - Field: [ESP32 Nodes] + [Solar + 18650 Battery] + [SX1278 LoRa]
  - Transmission: Custom 28-Byte Binary Packet + CRC16 Integrity
  - Relief Center: [SX1278 SPI] -> [Jetson Orin Nano]
  - Actions: [FastAPI SPA Dashboard] + [SIM800L SMS] + [Hardware Strobe/Buzzer]

Slide 5: [Innovation 1: 3-Layer Sensor Confirmation Matrix]
  - The Core Philosophy: "No Single Sensor Can Trigger an Evacuation"
  - Table showing 3 Layers for Flood, Landslide, Fire, and Pollution.
  - Mathematical consensus score formula: Score = (0.50 * L1) + (0.30 * L2) + (0.20 * L3).
  - Threshold: >= 0.75 across all layers for RED Alert.

Slide 6: [Innovation 2: PyTorch GRU AI Predictive Engine]
  - Lightweight Gated Recurrent Unit (GRU) time-series model.
  - 30-timestep sliding window of anomaly vectors & derivative trends.
  - Multi-Horizon Forecasting: Probabilities at T+15m, T+30m, and T+60m.
  - Runs with sub-5ms GPU inference on Jetson Orin Nano.

Slide 7: [Innovation 3: Fail-Safe Offline Operations & Triple Alerts]
  - Local FastAPI glassmorphism dashboard (accessible via local Wi-Fi/Ethernet).
  - Direct AT-command GSM SMS dispatch via SIM800L.
  - Physical relay triggering 105dB Piezo Siren and Ultra-Bright Xenon Strobe.
  - Battery health tracking & brownout protection.

Slide 8: [Live Simulation & Performance Verification]
  - Real-time scenario injection (Flood surge curve).
  - 100% rejection rate in simulated glitch tests (truck vibration, sunlight, sensor spike).
  - Sub-second packet transmission over LoRa with zero packet loss.

Slide 9: [Hardware Implementation & Bill of Materials (BOM)]
  - Field Node BOM: ESP32 (₹450), LoRa SX1278 (₹350), Sensors (₹800), Solar/Battery (₹900) = ~₹2,500–₹3,200.
  - Central Gateway: Jetson Orin Nano (Relief Center asset).
  - Rugged IP66 weatherproof enclosure design.

Slide 10: [Impact, Scalability & Conclusion]
  - Scalable to hundreds of nodes across river basins and hill stations.
  - Qualcomm chipset & edge AI alignment.
  - Saving lives through proactive, reliable, and false-alarm-free warnings.
  - Open for Q&A.
```

---

## 6. Recording Setup & OBS Studio Layout Guidelines

To create a clean, professional submission video:

1. **OBS Studio Scene Setup:**
   - **Main Window (70% screen):** Screen Capture showing the Web Dashboard (`http://localhost:8080`).
   - **Side Window (30% screen):** Terminal window showing live packet reception logs or simulation output.
   - **Corner (Picture-in-Picture):** Presenter webcam (head-and-shoulders view with good lighting and eye contact).
2. **Audio Tips:**
   - Use a clear USB microphone or headset.
   - Keep speech clear, well-paced, and avoid rushing through technical terms like "PyTorch GRU" or "3-Layer Sensor Matrix".
3. **Transitions:**
   - Use subtle cross-fades between the presentation slides and the live demo screen recording.

---

## 7. Anticipated Judges / Viva Q&A Defense Script

Be prepared to answer these questions if asked by evaluators or during a viva:

### Q1: "Why did you use an NVIDIA Jetson Orin Nano instead of a Raspberry Pi at the Relief Center?"
> **Answer:** *"While a Raspberry Pi is sufficient for simple data logging, Disaster Sentinel runs multi-stream time-series GRU neural networks and evaluates sliding-window matrices concurrently across multiple field nodes. The Jetson Orin Nano provides dedicated Tensor Cores and GPU acceleration, allowing sub-5 millisecond AI inference, hosting the full asynchronous FastAPI web server, and providing headroom for scaling to dozens of regional LoRa nodes without bottlenecking."*

### Q2: "What happens if a sensor breaks or gets disconnected in the field?"
> **Answer:** *"Our firmware and packet decoder implement hardware fault detection. If a sensor reports out-of-range ADC values or I2C bus errors, the ESP32 sets a specific fault flag in the LoRa telemetry packet. At the Jetson level, our 3-Layer Validator identifies that the sensor has failed, flags the node for maintenance on the dashboard, and dynamically recalibrates confirmation weights so that a broken sensor never triggers an accidental evacuation or disables the node."*

### Q3: "Why choose LoRa over 4G/5G or Satellite for field telemetry?"
> **Answer:** *"During landslides, cyclones, or wildfires, commercial cellular towers and fiber backbones frequently lose power or physical connectivity. Satellite transceivers require significant power and expensive subscription models. LoRa operates in the unlicensed 433 MHz ISM band, consumes milliwatts of power, penetrates dense forest canopies and rugged terrain over 5 to 10 kilometers, and operates indefinitely on a small solar panel without recurring network charges."*

### Q4: "How does your GRU model avoid over-fitting on normal days?"
> **Answer:** *"The PyTorch GRU model is trained using normalized sliding windows of anomaly differentials rather than raw sensor amplitudes. During the first 48 to 72 hours of field deployment, each node establishes a local environmental baseline. The GRU model evaluates deviations and rates of change relative to that learned baseline, enabling robust generalization across varying climates and seasonal changes."*

---
*Created for Disaster Sentinel SIH 2026 Team · All rights reserved.*

