/**
 * Disaster Sentinel — Node 2 (Landslide) Configuration
 * 
 * ESP32 Node SLD2:
 *   - Layer 1: MPU6050 Tilt & Vibration
 *   - Layer 2: Capacitive Soil Moisture
 *   - Layer 3: BME280 Barometric Pressure & Storm Context
 */

#ifndef CONFIG_H
#define CONFIG_H

#ifndef NODE_ID
#define NODE_ID "SLD2"
#endif

#ifndef NODE_TYPE
#define NODE_TYPE 0x03  // LANDSLIDE
#endif

#define LAYER_COUNT 3

// LoRa SPI Pins
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

// Sensor Pins
#define MPU_ADDR           0x68
#define SOIL_ANALOG_PIN    32
#define BME_SDA            21
#define BME_SCL            22
#define BME_ADDR           0x76

// 3-Layer Weights
#define SLIDE_LAYER1_WEIGHT 0.50f   // MPU6050 tilt
#define SLIDE_LAYER2_WEIGHT 0.30f   // Soil moisture
#define SLIDE_LAYER3_WEIGHT 0.20f   // Pressure

#define PRIORITY_THRESHOLD  0.70f
#define ELEVATED_THRESHOLD  0.50f

#define NORMAL_INTERVAL_MS   120000  // 2 min
#define ALERT_INTERVAL_MS    15000   // 15 sec
#define ELEVATED_INTERVAL_MS 30000   // 30 sec

#define BATTERY_ADC_PIN      36
#define BATTERY_FULL_MV      4200
#define BATTERY_EMPTY_MV     3000

#define PACKET_HEADER_NORMAL   0xAA
#define PACKET_HEADER_PRIORITY 0xFF

#endif // CONFIG_H
