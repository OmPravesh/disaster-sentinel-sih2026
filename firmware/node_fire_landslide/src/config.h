/**
 * Disaster Sentinel — Node 2 (Fire + Landslide) Configuration
 * 
 * This node monitors TWO hazard types simultaneously:
 *   - Fire:      Flame sensor + Gas sensor + BME280
 *   - Landslide: MPU6050 + Soil moisture + BME280 (shared)
 * 
 * Sends two types of LoRa packets per cycle.
 */

#ifndef CONFIG_H
#define CONFIG_H

// ============================================================
// NODE IDENTITY
// ============================================================
#ifndef NODE_ID
#define NODE_ID "FIR2"
#endif

#ifndef NODE_TYPE
#define NODE_TYPE 0x02  // FIRE (primary)
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

// --- FIRE SENSORS ---

// Flame/IR Sensor (KY-026)
#define FLAME_ANALOG_PIN   34  // ADC1_CH6
#define FLAME_DIGITAL_PIN  27

// Gas Sensor (MQ-2)
#define GAS_ANALOG_PIN     35  // ADC1_CH7
#define GAS_DIGITAL_PIN    26
// NOTE: MQ-2 heater needs 5V — powered from separate regulator

// --- LANDSLIDE SENSORS ---

// MPU6050 (I2C)
#define MPU_ADDR           0x68

// Soil Moisture (Capacitive v1.2)
#define SOIL_ANALOG_PIN    32  // ADC1_CH4

// --- SHARED ---

// BME280 (I2C — shared between Fire L3 and Landslide L3)
#define BME_SDA  21
#define BME_SCL  22
#define BME_ADDR 0x76

// ============================================================
// ANOMALY DETECTION PARAMETERS
// ============================================================

#define ANOMALY_Z_THRESHOLD     2.0f
#define BASELINE_MIN_SAMPLES    100

#ifndef BASELINE_DURATION_HOURS
#define BASELINE_DURATION_HOURS 48
#endif

// Fire 3-Layer weights
#define FIRE_LAYER1_WEIGHT  0.50f   // Flame sensor
#define FIRE_LAYER2_WEIGHT  0.30f   // Gas/smoke
#define FIRE_LAYER3_WEIGHT  0.20f   // BME280 (temp spike + humidity drop)

// Landslide 3-Layer weights
#define SLIDE_LAYER1_WEIGHT 0.50f   // MPU6050 tilt/vibration
#define SLIDE_LAYER2_WEIGHT 0.30f   // Soil moisture
#define SLIDE_LAYER3_WEIGHT 0.20f   // BME280 (rain conditions)

// Thresholds
#define PRIORITY_THRESHOLD   0.70f
#define ELEVATED_THRESHOLD   0.50f

// ============================================================
// TIMING
// ============================================================

#ifndef NORMAL_INTERVAL_MS
#define NORMAL_INTERVAL_MS 120000  // 2 minutes
#endif
#ifndef ALERT_INTERVAL_MS
#define ALERT_INTERVAL_MS 15000    // 15 seconds
#endif
#define ELEVATED_INTERVAL_MS 30000  // 30 seconds

#define SENSOR_WARMUP_MS    500
#define MQ2_WARMUP_MS       20000  // MQ-2 needs 20 sec heater warm-up

// ============================================================
// POWER MANAGEMENT
// ============================================================

#define BATTERY_ADC_PIN    36  // ADC1_CH0
#define BATTERY_FULL_MV    4200
#define BATTERY_EMPTY_MV   3000
#define DEEP_SLEEP_NORMAL_US  (NORMAL_INTERVAL_MS * 1000ULL)
#define DEEP_SLEEP_ALERT_US   (ALERT_INTERVAL_MS * 1000ULL)

// MQ-2 heater control (turn off during sleep to save power)
#define MQ2_HEATER_PIN     25  // GPIO to control MQ-2 heater via MOSFET

// ============================================================
// PACKET FORMAT
// ============================================================

#define PACKET_HEADER_NORMAL   0xAA
#define PACKET_HEADER_PRIORITY 0xFF

#endif // CONFIG_H
