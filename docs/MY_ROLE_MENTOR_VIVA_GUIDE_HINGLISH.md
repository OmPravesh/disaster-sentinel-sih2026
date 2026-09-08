# Disaster Sentinel: Meri Responsibilities, Data Engineering, ML Training aur Website Architecture Guide (Hinglish)

> **Document Type:** Personal SIH Mentor & Jury Viva Preparation Guide  
> **My Core Roles:**  
> 1. Real-World Data Collection & Data Governance  
> 2. Data Cleaning, Filtering & Hardware Alignment Preprocessing  
> 3. Dual-Brain AI Model Training (Random Forest + PyTorch 2-Layer GRU)  
> 4. Central Command Web Platform & Real-Time Telemetry API Development  

---

## 🎯 1. 30-Second Elevator Pitch (Jab Mentor Pooche: "Aapka Kaam Kya Tha?")

Jab mentor ya judge pooche: *"Aapne is project mein kya contribute kiya?"*, toh confident hokar ye bolna:

> *"Sir / Ma'am, is project mein mera primary role **Data Engineering**, **Dual-Brain AI Model Training**, aur **Central Command Web Platform Development** tha.*
> 
> *Sabse pehle, maine charo hazards—**Flood, Landslide, Fire, aur Air Pollution**—ke liye authoritative government agencies jaise **CWC, IMD, GSI, aur CPCB** se real-world telemetry data collect aur curate kiya.*
> 
> *Data ko clean karte waqt maine ensure kiya ki model kisi artificial timestamp ya packet counter pe overfit na ho, aur feature space ko strictly hamare **ESP32 physical sensors** ke sath align kiya.*
> 
> *Model training mein maine ek **Dual-Brain AI Architecture** implement kiya: pehla, **Random Forest Tripwire** jo sub-2 milliseconds mein current state classify karta hai; aur doosra, ek **2-Layer PyTorch GRU Recurrent Neural Network** jo rolling time-series sequence ko analyze karke **agale 10 se 50 minutes ka trajectory forecast** aur **Early Warning Lead Time** nikalta hai.*
> 
> *Finally, maine **Central Command Web Dashboard (Flask + Leaflet GIS + Chart.js)** develop kiya aur ek real-time `/api/telemetry` pipeline banayi jisse physical ESP32 nodes ka live LoRa data seedha website aur AI engine mein stream hota hai."*

---

## 📊 2. Real-World Data Collection (Data Kahan Se Aaya?)

Agar mentor pooche: *"Data kahan se laya? Kya synthetic data pe train kiya hai?"*  
Toh batana ki humne **real-world authoritative datasets** use kiye hain:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          REAL-WORLD DATA SOURCES                             │
├──────────────┬──────────────────────────────┬───────────────────────────────┤
│ Domain       │ Agency / Benchmark           │ Real Telemetry Captured       │
├──────────────┼──────────────────────────────┼───────────────────────────────┤
│ 1. Flood     │ Central Water Commission     │ Upper Ganga Basin (Rishikesh) │
│    (FLD1)    │ (CWC) + IMD Monsoon Records  │ River water levels (m), rain  │
│              │                              │ rate (mm/hr), barometric hPa  │
├──────────────┼──────────────────────────────┼───────────────────────────────┤
│ 2. Landslide │ Geological Survey of India   │ Chamoli Garhwal Slope Data:   │
│    (SLD2)    │ (GSI) + NASA Landslide Cat.  │ Inclinometer tilt angles (°), │
│              │                              │ soil moisture saturation, rain│
├──────────────┼──────────────────────────────┼───────────────────────────────┤
│ 3. Wildfire  │ IoT Smoke Detection          │ 62,630 empirical sensor rows: │
│    (FIR3)    │ Benchmark Dataset (Kaggle)   │ TVOC (ppb), eCO2 (ppm), flame │
│              │                              │ IR, temperature, humidity     │
├──────────────┼──────────────────────────────┼───────────────────────────────┤
│ 4. Pollution │ Central Pollution Control    │ Continuous Ambient Air Quality│
│    (POL4)    │ Board (CPCB) CAAQMS          │ Monitoring: NO2, CO, PM10,    │
│              │                              │ PM2.5 industrial levels       │
└──────────────┴──────────────────────────────┴───────────────────────────────┘
```

### 💡 Mentor ko explain karne ke points:
1. **Flood Data:** Uttarakhand ke Rishikesh river gauge station ka hydrograph data use kiya hai jisme monsoon cloudbursts aur sudden water surges record hue the.
2. **Landslide Data:** GSI ke Himalayan slope transects ka geotechnical data hai, jisme slope tilt aur volumetric soil saturation ka correlation measure kiya gaya hai.
3. **Fire Data:** Controlled test fires ka multi-sensor data hai jisme hydrocarbon combustion gases, flame radiation aur temperature spikes simultaneously record hue the.
4. **Pollution Data:** CPCB ke industrial monitoring stations (jaise Selaqui Dehradun) ka air pollution data hai jisme hazardous $PM_{2.5}$ aur $NO_2$ smog inversions record hue the.

---

## 🧹 3. Data Cleaning & Preprocessing (Data Ko Clean Kaise Kiya?)

Ye part mentors ke liye **sabse important** hota hai. Hamari script hai: [`ai/preprocess.py`](file:///c:/Users/adity/OneDrive/Desktop/Disaster%20Management%20System/disaster-sentinel-sih2026/ai/preprocess.py).

```
RAW CSV DATA ──> [1. Leakage Pruning] ──> [2. Hardware Alignment] ──> [3. 3-Tier Mapping] ──> [4. Stratified Split]
```

### Step 1: Artificial Data Leakage Columns Hataye
* **Problem:** Raw datasets mein `Unnamed: 0` (index), `UTC` (timestamp), aur `CNT` (packet counter) jaise columns hote hain. Agar model inko padh le, toh wo timestamp rat lega aur fake 100% accuracy dikhayega.
* **Mera Solution:** Maine script mein `df.drop(columns=['Unnamed: 0', 'UTC', 'CNT'])` lagakar in columns ko completely delete kiya. Model ab sirf **real physics aur chemistry** (temperatures, gases, water levels) seekhta hai.

### Step 2: Physical Hardware Alignment
* **Problem:** CPCB ya online datasets mein aisi gases bhi hoti hain jo hamare hardware pe sensor nahi hai (jaise $SO_2$ ya Ozone $O_3$).
* **Mera Solution:** Maine dataset ko filter karke sirf wahi features rakhe jo hamare **ESP32 ke physical sensors** measure kar sakte hain:
  * Flood: Water Level, Rain Rate, Pressure, Temp, Humidity.
  * Landslide: Slope Tilt, Soil Moisture, Rainfall.
  * Fire: Flame IR, Smoke/TVOC, Temperature.
  * Pollution: $CO$, $NO_2$, $PM_{2.5}$, $PM_{10}$.

### Step 3: Reclassification into 3-Tier Emergency Scheme
* **Problem:** Raw data mein ajeeb remarks the: *"Satisfactory"*, *"Moderate"*, *"Unhealthy for Sensitive Groups"*, *"Severe"*. Emergency team ko exact alert chahiye.
* **Mera Solution:** Maine custom mapping function likhkar data ko **3 actionable disaster tiers** mein categorize kiya:
  * **`Safe` (Green):** Normal range.
  * **`Warning` (Yellow/Orange):** Anomaly detected; 3-second rapid priority telemetry active.
  * **`Hazardous` (Red):** Critical threshold breached with multi-layer consensus; siren, strobe aur NDRF SOS trigger.

### Step 4: Stratified 80/20 Train-Test Split
* Rare disaster events (Hazardous) training aur testing dono mein barabar ratio mein aayein, iske liye maine `train_test_split(..., stratify=y)` use kiya.

---

## 🧠 4. Model Training: Dual-Brain AI Architecture (AI Kaise Train Kiya?)

Humne ek nahi, balki **do AI models (Dual-Brain)** train kiye hain:

```
Incoming Sensor Reading 
      │
      ├──> [Brain 1: Random Forest] ────> Instant Status: Safe / Warning / Hazardous (1.4 ms)
      │
      └──> [Brain 2: PyTorch GRU]   ────> Future Forecast (+10m to +50m) & Lead Time (8.2 ms)
```

### Brain 1: Random Forest Fast Tripwire Classifier ([`ai/train_rf.py`](file:///c:/Users/adity/OneDrive/Desktop/Disaster%20Management%20System/disaster-sentinel-sih2026/ai/train_rf.py))
* **Algorithm:** `RandomForestClassifier(n_estimators=100, random_state=42)`
* **Kaise kaam karta hai:** 100 decision trees milkar vote karte hain.
* **Kyun use kiya?**
  * Instant inference: **$1.4\text{ ms}$** mein execute hota hai.
  * Feature scaling ki zaroorat nahi hoti (water level meters mein ho aur pressure hPa mein ho, dono ko perfectly handle karta hai).
  * Overfitting nahi hoti kyunki 100 trees ka average liya jata hai.
* **Accuracy:**
  * Flood (`FLD1`): **99.15%**
  * Landslide (`SLD2`): **98.43%**
  * Fire (`FIR3`): **99.88%**
  * Pollution (`POL4`): **98.72%**
* **Output Format:** Model ko `.joblib` format mein export kiya `models/` directory mein.

---

### Brain 2: PyTorch 2-Layer GRU Recurrent Forecaster ([`ai/train_gru.py`](file:///c:/Users/adity/OneDrive/Desktop/Disaster%20Management%20System/disaster-sentinel-sih2026/ai/train_gru.py))
* **Architecture:** Deep Recurrent Neural Network (`DisasterGRUForecaster`):
  * Input: Pichle 10 timesteps ka sequence window.
  * 2 Stacked GRU Layers (64 hidden units each, with Dropout 0.2).
  * Dual Output Heads:
    1. **Regression Head:** Agale 5 future steps predict karta hai (**+10m, +20m, +30m, +40m, +50m**).
    2. **Classification Head:** Probability $P(\text{Disaster at } T+30\text{m})$ nikalta hai.
* **Kyun use kiya GRU instead of LSTM or Transformers?**
  * GRU mein LSTM se **33% kam parameters** hote hain (sirf Reset gate aur Update gate).
  * Edge devices (NVIDIA Jetson Orin Nano / Qualcomm NPU) par bina heat ya memory lag ke **$8.2\text{ ms}$** mein run hota hai.
  * Transformers ki tarah quadratic memory compute nahi mangta.
* **Multi-Task Loss:**
  $$\mathcal{L} = \mathcal{L}_{MSE}(\text{Future Trajectory}) + 0.5 \cdot \mathcal{L}_{BCE}(\text{Risk Probability})$$
* **Early Warning Lead Time:**
  Agar GRU dekhta hai ki t+20m par water level critical threshold ($10\text{ m}$) cross karega, toh wo dashboard par label karta hai:  
  👉 **`"BREACH PREDICTED IN 20 MINS"`**  
  Isse NDRF aur local police ko disaster aane se **20 minute pehle evacuation** ka time mil jata hai!

---

## 🌐 5. Website & Central Command Dashboard (Website Mein Kya Implement Kiya?)

Hamara web server [`web/server.py`](file:///c:/Users/adity/OneDrive/Desktop/Disaster%20Management%20System/disaster-sentinel-sih2026/web/server.py) Flask framework par built hai.

### Mera Contribution Website Mein:
1. **Real-Time Telemetry Ingestion Pipeline (`/api/telemetry`):**
   * Maine ek dedicated REST endpoint banaya.
   * Chahe data physical LoRa gateway se aaye ya laptop par USB serial bridge se aaye, ye endpoint JSON payload receive karta hai.
   * Ye sensor data ko extract karta hai, rolling sequence buffer mein push karta hai, aur **instantaneously Random Forest aur PyTorch GRU run karta hai**.
2. **7-Page Enterprise Web Platform:**
   * **Overview Page (`/`):** Leaflet.js interactive GIS map jisme Uttarakhand ke 4 nodes pinned hain. Live health cards aur battery status.
   * **Live Monitoring (`/monitoring`):** Real-time physical gauges (Water level, Tilt angle, TVOC gas, $PM_{2.5}$ dust).
   * **Disaster Map (`/map`):** High-resolution topological hazard heatmaps.
   * **Alerts & Emergency (`/alerts`):** Automated incident management queue (`INC-101`, `INC-102`) aur automated **GSM SIM800L NDRF SMS dispatch**.
   * **Analytics & ML (`/analytics`):** Chart.js live trend curves jisme **actual sensor readings ke sath GRU ki dotted future forecast trajectory** plot hoti hai.
   * **Hardware Page (`/hardware`):** LoRa SPI bus state, frequency (433.0 MHz), GPIO buzzer/strobe controls.
   * **System About Page (`/about`):** Bill of Materials aur architecture specs.
3. **Interactive Simulation Triggers for Live Presentation:**
   * Header mein **"Simulate Flash Flood"**, **"Simulate Landslide"**, etc. ke buttons hain.
   * Presentation ke time jab hum button click karte hain, toh background mein real PyTorch GRU model execute hota hai aur screen par real-time lead-time aur red alerts change hote hain.

---

## 🎤 6. Mentor & Jury Cross-Questioning FAQ (Ready Answers!)

### ❓ Q1: "Data cleaning mein sabse challenging cheez kya thi?"
> **Aapka Jawab:**  
> *"Sir, sabse challenging part tha **data leakage remove karna** aur **physical hardware alignment**. 
> Raw internet datasets mein timestamps aur row counters hote the jinpar model artificially overfit ho jata tha. Maine unhe drop kiya aur feature space ko strictly filter karke sirf wahi features rakhe jo hamare ESP32 nodes ke physical sensors measure karte hain."*

---

### ❓ Q2: "Random Forest aur Deep Learning (GRU) dono kyun use kiye? Ek hi kaafi nahi tha?"
> **Aapka Jawab:**  
> *"Sir, dono ka purpose alag hai:
> * **Random Forest (Tripwire):** Ek instant snapshot classifier hai. Ye sub-2 milliseconds mein batata hai ki *is second* situation Safe hai ya Hazardous.
> * **PyTorch GRU (Predictive AI):** Ek temporal recurrent model hai. Sirf current state janana kaafi nahi hota; hume momentum dekhna hota hai ki water level kitni tezi se badh raha hai. GRU pichle 10 readings ko dekh kar **agale 50 minutes ka forecast** nikalta hai aur **Early Warning Lead Time** calculate karta hai."*

---

### ❓ Q3: "Model overfit toh nahi ho gaya? 99% accuracy suspicious lagti hai!"
> **Aapka Jawab:**  
> *"Sir, humne strictly prevent kiya hai:
> 1. Testing hamesha ek **independent 20% stratified test set** par hui hai jo model ne training mein kabhi nahi dekhi.
> 2. Random Forest mein 100 decorrelated trees vote karte hain jo variance suppress karta hai.
> 3. PyTorch GRU mein humne **0.2 Dropout** use kiya hai to prevent co-adaptation.
> 4. Aur sabse bada safeguard hamara **3-Layer Physical Sensor Consensus** hai—ek sensor ka glitch kabhi false alarm nahi bana sakta jab tak baaki ke independent physical sensors use corroborate na karein."*

---

### ❓ Q4: "Agar physical sensor se NaN ya corrupted data aa jaye toh kya website ya AI crash ho jayegi?"
> **Aapka Jawab:**  
> *"Nahi sir, humne fail-safe exception handling likhi hai:
> * Firmware level par agar sensor read nahi hota toh node fallback baseline flag ke sath packet bhejta hai.
> * Web server level par `/api/telemetry` endpoint mein missing values rolling sequence buffer ke previous valid mean se impute hoti hain.
> * System crash hone ke bajaye 3-layer se 2-layer mode mein gracefully downscale ho jata hai."*

---

### ❓ Q5: "Website par real-time data kaise aata hai?"
> **Aapka Jawab:**  
> *"Sir, field nodes 433 MHz LoRa radio packets bhejte hain. 
> Gateway hub (NVIDIA Jetson ya laptop) par hamara receiver script packet ko decode karke `/api/telemetry` par HTTP POST karta hai.
> Server par data aate hi models inference karte hain, aur frontend har 1 second mein lightweight `/api/nodes` polling se Chart.js aur Leaflet GIS map ko update karta hai bina page reload kiye."*

---

*Authored for Smart India Hackathon 2026 · Problem Statement SIH26178 (Qualcomm) · Repository: [OmPravesh/disaster-sentinel-sih2026](https://github.com/OmPravesh/disaster-sentinel-sih2026)*

