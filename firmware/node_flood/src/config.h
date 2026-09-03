/**
 * Disaster Sentinel — Node 1 (Flood) Configuration
 * 
 * Pin assignments, thresholds, and system parameters.
 * All configurable values are centralized here.
 */

#ifndef CONFIG_H
#define CONFIG_H

// ============================================================
// NODE IDENTITY
// ============================================================
#ifndef NODE_ID
#define NODE_ID "FLD1"
#endif

#ifndef NODE_TYPE
#define NODE_TYPE 0x01  // FLOOD
#endif

// ============================================================
// LoRa SX1278 Pin Assignments (SPI)
// ============================================================
#define LORA_SCK   18
#define LORA_MISO  19
#define LORA_MOSI  23
#define LORA_CS    5
#define LORA_RST   14
#define LORA_DIO0  2

// LoRa Parameters
#ifndef LORA_FREQUENCY
#define LORA_FREQUENCY 433E6
#endif

#ifndef LORA_TX_POWER
#define LORA_TX_POWER 17
#endif

#ifndef LORA_SPREADING_FACTOR
#define LORA_SPREADING_FACTOR 7
#endif

#ifndef LORA_BANDWIDTH
#define LORA_BANDWIDTH 125E3
#endif

// ============================================================
// SENSOR PIN ASSIGNMENTS
// ============================================================

// Water Level Sensor (Ultrasonic JSN-SR04T)
#define WATER_TRIG_PIN  13
#define WATER_ECHO_PIN  12

// Water Level Sensor (Analog fallback)
#define WATER_ANALOG_PIN 34  // ADC1_CH6

// Rain Sensor (YL-83)
#define RAIN_ANALOG_PIN  35  // ADC1_CH7
#define RAIN_DIGITAL_PIN 4

// BME280 (I2C)
#define BME_SDA  21
#define BME_SCL  22
#define BME_ADDR 0x76

// ============================================================
// ANOMALY DETECTION PARAMETERS
// ============================================================

// Z-score threshold for anomaly detection
#define ANOMALY_Z_THRESHOLD     2.0f

// Minimum readings before baseline is valid
#define BASELINE_MIN_SAMPLES    100

// Baseline collection duration (hours)
#ifndef BASELINE_DURATION_HOURS
#define BASELINE_DURATION_HOURS 48
#endif

// 3-Layer confidence weights
#define LAYER1_WEIGHT  0.50f   // Primary sensor (water level)
#define LAYER2_WEIGHT  0.30f   // Corroborating (rain)
#define LAYER3_WEIGHT  0.20f   // Context (BME280 pressure/humidity)

// Combined score threshold for priority packets
#define PRIORITY_THRESHOLD   0.70f
#define ELEVATED_THRESHOLD   0.50f

// ============================================================
// TIMING
// ============================================================

// Normal transmission interval (ms)
#ifndef NORMAL_INTERVAL_MS
#define NORMAL_INTERVAL_MS 120000  // 2 minutes
#endif

// Alert transmission interval (ms)
#ifndef ALERT_INTERVAL_MS
#define ALERT_INTERVAL_MS 15000  // 15 seconds
#endif

// Elevated transmission interval (ms)
#define ELEVATED_INTERVAL_MS 30000  // 30 seconds

// Sensor warm-up time (ms)
#define SENSOR_WARMUP_MS 500

// ============================================================
// POWER MANAGEMENT
// ============================================================

// Battery ADC pin (voltage divider)
#define BATTERY_ADC_PIN 36  // ADC1_CH0

// Battery voltage thresholds (for 2x 18650 in parallel, 3.7V nominal)
#define BATTERY_FULL_MV   4200
#define BATTERY_EMPTY_MV  3000

// Deep sleep configuration
#define DEEP_SLEEP_NORMAL_US  (NORMAL_INTERVAL_MS * 1000ULL)
#define DEEP_SLEEP_ALERT_US   (ALERT_INTERVAL_MS * 1000ULL)

// ============================================================
// FLOOD-SPECIFIC THRESHOLDS (used alongside anomaly detection)
// ============================================================

// Water level danger threshold (cm) — informational, anomaly detection is primary
#define WATER_DANGER_CM    200.0f
#define WATER_WARNING_CM   150.0f

// Rain intensity threshold (analog 0-4095, lower = more rain for YL-83)
#define RAIN_HEAVY_THRESHOLD  1500
#define RAIN_LIGHT_THRESHOLD  3000

// Barometric pressure drop indicating storm (hPa)
#define PRESSURE_STORM_DROP  5.0f   // Drop of 5 hPa from baseline

// ============================================================
// PACKET FORMAT
// ============================================================

#define PACKET_HEADER_NORMAL   0xAA
#define PACKET_HEADER_PRIORITY 0xFF

#endif // CONFIG_H
