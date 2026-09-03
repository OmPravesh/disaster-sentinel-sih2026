/**
 * Disaster Sentinel — Sleep/Power Manager Implementation
 */

#include "sleep_manager.h"
#include <esp_sleep.h>

// Battery voltage mapping constants
// Assuming voltage divider: R1=100K, R2=100K (divides by 2)
// ESP32 ADC reads 0-3.3V (with 11dB attenuation)
// So battery range 3.0V-4.2V maps to ADC range 1.5V-2.1V
static const float VOLTAGE_DIVIDER_RATIO = 2.0f;
static const float ADC_REF_VOLTAGE = 3.3f;
static const float ADC_MAX_VALUE = 4095.0f;

void SleepManager::begin(int batteryPin) {
    _batteryPin = batteryPin;

    if (_batteryPin >= 0) {
        analogSetAttenuation(ADC_11db);
        Serial.printf("[SleepMgr] Battery monitoring on GPIO%d\n", _batteryPin);
    } else {
        Serial.println("[SleepMgr] No battery monitoring configured");
    }
}

uint8_t SleepManager::readBatteryPercent() {
    if (_batteryPin < 0) return 100;  // No monitoring — assume full

    uint32_t mv = readBatteryMV();

    // Map 3000mV-4200mV to 0-100%
    if (mv <= 3000) return 0;
    if (mv >= 4200) return 100;

    return (uint8_t)((mv - 3000) * 100 / 1200);
}

uint32_t SleepManager::readBatteryMV() {
    if (_batteryPin < 0) return 4200;  // Assume full

    // Average multiple ADC readings for stability
    long sum = 0;
    const int samples = 20;

    for (int i = 0; i < samples; i++) {
        sum += analogRead(_batteryPin);
        delayMicroseconds(100);
    }

    float avgAdc = (float)sum / samples;

    // Convert ADC reading to voltage
    float adcVoltage = (avgAdc / ADC_MAX_VALUE) * ADC_REF_VOLTAGE;

    // Apply voltage divider ratio to get actual battery voltage
    float batteryVoltage = adcVoltage * VOLTAGE_DIVIDER_RATIO;

    return (uint32_t)(batteryVoltage * 1000.0f);  // Convert to millivolts
}

void SleepManager::deepSleep(uint64_t durationUs) {
    Serial.printf("[SleepMgr] Entering deep sleep for %llu ms\n", durationUs / 1000);
    Serial.flush();

    esp_sleep_enable_timer_wakeup(durationUs);
    esp_deep_sleep_start();

    // Code below this line never executes — ESP32 resets on wake
}

void SleepManager::adaptiveSleep(float combinedScore,
                                  uint64_t normalUs,
                                  uint64_t elevatedUs,
                                  uint64_t alertUs) {
    uint64_t sleepDuration;

    if (combinedScore >= 0.70f) {
        // Alert state — minimal sleep for rapid updates
        sleepDuration = alertUs;
        Serial.println("[SleepMgr] State: ALERT — minimal sleep");
    } else if (combinedScore >= 0.50f) {
        // Elevated state — moderate sleep
        sleepDuration = elevatedUs;
        Serial.println("[SleepMgr] State: ELEVATED — moderate sleep");
    } else {
        // Normal state — full sleep for battery conservation
        sleepDuration = normalUs;
        Serial.println("[SleepMgr] State: NORMAL — full sleep");
    }

    deepSleep(sleepDuration);
}

bool SleepManager::isBatteryCritical() {
    return readBatteryPercent() < 10;
}
