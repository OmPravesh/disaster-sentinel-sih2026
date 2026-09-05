"""
Disaster Sentinel — Air Pollution Event Simulation Scenario

Simulates severe industrial/air pollution event:
  Phase 1: Clean air baseline (AQI ~45, PM2.5 ~12)
  Phase 2: Rising particulate matter & toxic gases (Layer 1 & 2 anomalous)
  Phase 3: Hazardous Air Quality Index (RED alert — 2-layer CONFIRMED)
  Phase 4: Dispersion / returning to baseline
"""

import sys
import os
import asyncio
import logging

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "jetson"))

from simulation.fake_node import _build_raw_packet, HAZARD_POLLUTION
try:
    from receiver.packet_decoder import decode_packet, format_packet_log
except ImportError:
    from jetson.receiver.packet_decoder import decode_packet, format_packet_log

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger("scenario_pollution")


async def run_pollution_scenario(on_packet_cb=None):
    logger.info("==================================================")
    logger.info("  STARTING AIR POLLUTION SIMULATION SCENARIO")
    logger.info("==================================================")

    seq = 4000
    
    timeline = [
        (5, 45.0, 12.0, 0.05, 0.04, 0, "NORMAL: Good air quality (AQI 45, PM2.5 12 ug/m3)"),
        (5, 120.0, 48.0, 0.35, 0.30, 1, "MODERATE POLLUTION: AQI 120, PM2.5 rising (YELLOW)"),
        (5, 240.0, 115.0, 0.72, 0.68, 3, "UNHEALTHY AIR: AQI 240, PM2.5 115 ug/m3 (ORANGE)"),
        (5, 380.0, 220.0, 0.94, 0.90, 3, "HAZARDOUS ALERT: AQI 380 (HAZARDOUS), 2-layer CONFIRMED (RED)"),
        (5, 60.0, 18.0, 0.12, 0.10, 2, "DISPERSION: Air quality improving post-ventilation"),
    ]

    for step in timeline:
        duration, aqi, pm25, l1_a, l2_a, rate, desc = step
        logger.info(f"\n▶ SCENARIO STEP: {desc}")
        
        combined = 0.55 * l1_a + 0.45 * l2_a
        is_priority = combined > 0.70

        raw_packet = _build_raw_packet(
            "POL4", HAZARD_POLLUTION,
            aqi, l1_a,
            pm25, l2_a,
            0.0, 0.0,
            combined,
            rate,
            88,
            seq,
            priority=is_priority
        )

        pkt = decode_packet(raw_packet, rssi=-46)
        logger.info(format_packet_log(pkt))

        if on_packet_cb:
            if asyncio.iscoroutinefunction(on_packet_cb):
                await on_packet_cb(pkt)
            else:
                on_packet_cb(pkt)

        seq += 1
        await asyncio.sleep(duration)

    logger.info("==================================================")
    logger.info("  POLLUTION SCENARIO COMPLETED")
    logger.info("==================================================")


if __name__ == "__main__":
    asyncio.run(run_pollution_scenario())
