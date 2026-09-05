"""
Disaster Sentinel — Fire Event Simulation Scenario

Simulates fire ignition and spread:
  Phase 1: Normal ambient temperature and clean air
  Phase 2: Smoke/gas buildup (Layer 2 anomalous)
  Phase 3: Flame detection + smoke + temperature spike (RED alert — 3-layer confirmed)
"""

import sys
import os
import asyncio
import logging

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "jetson"))

from simulation.fake_node import _build_raw_packet, HAZARD_FIRE
from receiver.packet_decoder import decode_packet, format_packet_log

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger("scenario_fire")


async def run_fire_scenario(on_packet_cb=None):
    logger.info("==================================================")
    logger.info("  STARTING FIRE EVENT SIMULATION SCENARIO")
    logger.info("==================================================")

    seq = 2000
    
    timeline = [
        (5, 0.01, 0.05, 27.5, 0.02, 0.04, 0.03, 0, "NORMAL: Ambient conditions 27.5°C, clean air"),
        (5, 0.05, 0.35, 29.0, 0.08, 0.45, 0.15, 1, "SMOKE DETECTED: MQ-2 detecting early smoke accumulation"),
        (5, 0.45, 0.65, 38.5, 0.55, 0.72, 0.50, 3, "ORANGE ALERT: Flame IR triggered + rising smoke"),
        (5, 0.88, 0.85, 52.0, 0.92, 0.89, 0.84, 3, "RED ALERT: WILDFIRE CONFIRMED! 3-layer confirmation (Flame+Smoke+Temp Spike)"),
        (5, 0.95, 0.92, 65.0, 0.98, 0.95, 0.92, 3, "CRITICAL RED: Intense fire conditions"),
        (5, 0.10, 0.20, 32.0, 0.15, 0.25, 0.20, 2, "FIRE EXTINGUISHED / RECOVERY"),
    ]

    for step in timeline:
        duration, flame, gas, temp, l1_a, l2_a, l3_a, rate, desc = step
        logger.info(f"\n▶ SCENARIO STEP: {desc}")
        
        combined = 0.50 * l1_a + 0.30 * l2_a + 0.20 * l3_a
        is_priority = combined > 0.70

        raw_packet = _build_raw_packet(
            "FIR2", HAZARD_FIRE,
            flame, l1_a,
            gas, l2_a,
            temp, l3_a,
            combined,
            rate,
            88,
            seq,
            priority=is_priority
        )

        pkt = decode_packet(raw_packet, rssi=-42)
        logger.info(format_packet_log(pkt))

        if on_packet_cb:
            if asyncio.iscoroutinefunction(on_packet_cb):
                await on_packet_cb(pkt)
            else:
                on_packet_cb(pkt)

        seq += 1
        await asyncio.sleep(duration)

    logger.info("==================================================")
    logger.info("  FIRE SCENARIO COMPLETED")
    logger.info("==================================================")


if __name__ == "__main__":
    asyncio.run(run_fire_scenario())
