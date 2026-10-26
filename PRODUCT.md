# Product: Disaster Sentinel

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Primary Users:** Emergency Disaster Response Commanders, District Magistrates (SDMA/NDMA Uttarakhand), and Field Rescue Coordinators monitoring high-altitude multi-hazard risks.
- **Operating Context:** Mission-critical emergency operation centers (EOC) and edge field command posts operating 24/7 under fluctuating light conditions, managing real-time threats across river basins, landslide slopes, forest fire corridors, and industrial air pollution zones.

## Product Purpose

Disaster Sentinel is an autonomous multi-hazard disaster early-warning and telemetry intelligence platform. It fuses remote edge sensor nodes (SX1278 LoRa @ 433MHz) with Jetson Orin AI inference models (recurrent GRU forecaster) to predict environmental hazard breaches up to 50+ minutes before critical thresholds occur, enabling rapid evacuations and emergency containment.

## Core Capabilities

- **Multi-Hazard Edge Telemetry:** Real-time continuous ingest of river water depth (FLD1 ultrasonic), mountain slope incline and pore water pressure (SLD2 IMU/inclinometer), volatile combustion gases and TVOC (FIR3 SGP30/flame sensor), and particulate pollution (POL4 SDS011 PM2.5/PM10).
- **Recurrent AI Horizon Forecasting:** PyTorch-powered GRU recurrent model running locally on NVIDIA Jetson edge hardware, projecting 10m to 50m trajectory margins with 98.4% confidence.
- **Resilient Fallback Alerting:** SIM800L satellite/GSM SMS failover, auditory broadcast sirens, and instantaneous web push notifications when threshold limits are breached.
- **Interactive Simulation Engine:** Live parameter perturbation drawer allowing operators to simulate flood surges, slope instability, and wildfire flashovers for readiness drills.

## Durable Constraints & Standards

- **Life-Safety Interface Priority:** High-contrast, unambiguous visual hierarchy; no decorative distractions during emergency breaches.
- **Hardware Integration:** LoRa SX1278 point-to-point telemetry at 433MHz, SIM800L GSM fallback, Flask WebSocket/SSE real-time stream.
- **Accessibility & Ergonomics:** High-contrast dark mode to prevent operator fatigue during night watch; tabular numeric alignment on all high-frequency data streams.
