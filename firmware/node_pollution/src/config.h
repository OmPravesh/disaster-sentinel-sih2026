/**
 * Disaster Sentinel — Node 4 (Pollution) Configuration
 * 
 * 2-Layer Mode Node:
 *   - Layer 1: MQ-135 Air Quality / Gas Sensor
 *   - Layer 2: PM2.5 Dust Sensor (GP2Y1010AU0F / SDS011)
 *   - Layer 3: N/A (Bypassed)
 */

#ifndef CONFIG_H
#define CONFIG_H

// ============================================================
// NODE IDENTITY
// ============================================================
#ifndef NODE_ID
#define NODE_ID "POL4"
#endif

#ifndef NODE_TYPE
#define NODE_TYPE 0x04  // POLLUTION
#endif

#define LAYER_COUNT 2

// ============================================================
// LoRa SX1278 Pin Assignments (SPI)
// ============================================================
#define LORA_SCK   18
#define LORA_MISO  19
#define LORA_MOSI  23
#define LORA_CS    5
#define LORA_RST   14
#define LORA_DIO0  2

#define LORA_FREQUENCY        433E6
#define LORA_TX_POWER        17
#define LORA_SPREADING_FACTOR 7
#define LORA_BANDWIDTH        125E3

// ============================================================
// SENSOR PIN ASSIGNMENTS (2-Layer Mode)
// ============================================================

// Layer 1: MQ-135 Gas / Air Quality Sensor
#define MQ135_ANALOG_PIN    34  // ADC1_CH6
#define MQ135_DIGITAL_PIN   27

// Layer 2: PM2.5 Dust Sensor (Optical Dust Sensor GP2Y1010AU0F)
#define PM25_LED_PIN        12  // Drive LED pin
#define PM25_ANALOG_PIN     35  // ADC1_CH7 measure pin

// ============================================================
// 2-LAYER WEIGHTS & THRESHOLDS
// ============================================================
#define POL_LAYER1_WEIGHT   0.55f   // MQ-135 AQI
#define POL_LAYER2_WEIGHT   0.45f   // PM2.5 Dust

#define PRIORITY_THRESHOLD  0.70f
#define ELEVATED_THRESHOLD  0.50f

// ============================================================
// TIMING & POWER
// ============================================================
#define NORMAL_INTERVAL_MS   120000  // 2 minutes
#define ALERT_INTERVAL_MS    15000   // 15 seconds
#define ELEVATED_INTERVAL_MS 30000   // 30 seconds

#define BATTERY_ADC_PIN      36  // ADC1_CH0
#define BATTERY_FULL_MV      4200
#define BATTERY_EMPTY_MV     3000

#define PACKET_HEADER_NORMAL   0xAA
#define PACKET_HEADER_PRIORITY 0xFF

#endif // CONFIG_H
