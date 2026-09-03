/**
 * Disaster Sentinel — Sleep/Power Manager
 * 
 * Handles ESP32 deep sleep for battery conservation.
 * Sleep duration adapts based on anomaly state:
 *   - Normal:   2 minutes
 *   - Elevated: 30 seconds
 *   - Alert:    15 seconds
 */

#ifndef SLEEP_MANAGER_H
#define SLEEP_MANAGER_H

#include <Arduino.h>

class SleepManager {
public:
    /**
     * Initialize sleep manager.
     * @param batteryPin  ADC pin for battery voltage monitoring
     */
    void begin(int batteryPin = -1);

    /**
     * Read battery percentage (0-100).
     * Uses voltage divider: battery → R1 → ADC → R2 → GND
     * Assumes R1 = R2 = 100K (divides voltage by 2)
     */
    uint8_t readBatteryPercent();

    /**
     * Read raw battery voltage in millivolts.
     */
    uint32_t readBatteryMV();

    /**
     * Enter deep sleep for specified microseconds.
     * The ESP32 will reset on wake-up.
     */
    void deepSleep(uint64_t durationUs);

    /**
     * Enter deep sleep with duration based on anomaly state.
     * @param combinedScore  Current 3-layer combined anomaly score
     * @param normalUs       Sleep duration during normal operation
     * @param elevatedUs     Sleep duration during elevated state
     * @param alertUs        Sleep duration during alert state
     */
    void adaptiveSleep(float combinedScore,
                       uint64_t normalUs,
                       uint64_t elevatedUs,
                       uint64_t alertUs);

    /**
     * Check if battery is critically low.
     * @return true if battery < 10%
     */
    bool isBatteryCritical();

private:
    int _batteryPin;
};

#endif // SLEEP_MANAGER_H
