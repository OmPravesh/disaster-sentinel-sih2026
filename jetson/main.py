"""
═══════════════════════════════════════════════════════════
DISASTER SENTINEL — Main Orchestrator (v2.0)
═══════════════════════════════════════════════════════════

Ties together all subsystems:
  1. LoRa Receiver (or Simulated Receiver for testing)
  2. Packet Decoder
  3. Time-Series Store (SQLite)
  4. Three-Layer Validator (supports 2-layer and 3-layer nodes)
  5. Risk Predictor + GRU AI Predictor
  6. Alert Manager
  7. SMS / Buzzer / Strobe
  8. FastAPI Dashboard

Usage:
  # With simulated data (for development):
  python main.py --simulate

  # With real LoRa hardware:
  python main.py

  # Dashboard will be available at http://localhost:8080

SIH 2026 · Problem Statement SIH26178 · Qualcomm
═══════════════════════════════════════════════════════════
"""

import asyncio
import argparse
import logging
import os
import sys
import yaml
import uvicorn

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from receiver.packet_decoder import DecodedPacket, format_packet_log
from receiver.lora_receiver import LoRaReceiver, SimulatedReceiver
from data.time_series_store import TimeSeriesStore
from engine.three_layer_validator import ThreeLayerValidator
from engine.risk_predictor import RiskPredictor
from engine.alert_manager import AlertManager
from alerts.sms_sender import SMSSender
from alerts.buzzer_strobe import BuzzerControl, StrobeControl

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-7s | %(name)-20s | %(message)s',
    datefmt='%H:%M:%S',
)
logger = logging.getLogger("sentinel")


def load_config(path: str = "config.yaml") -> dict:
    """Load YAML configuration."""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    logger.warning(f"Config not found at {config_path}, using defaults")
    return {}


def clean_old_database(db_path: str):
    """
    Clean migration: delete old database if it exists.
    
    Since this is a dev/hackathon project, we wipe the old DB
    when upgrading from 2-node to 4-node architecture.
    The node IDs changed (FIR2 → FIR3, new POL4), so old data
    is incompatible.
    """
    full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), db_path)
    if os.path.exists(full_path):
        try:
            import sqlite3
            conn = sqlite3.connect(full_path)
            cursor = conn.execute(
                "SELECT DISTINCT node_id FROM sensor_readings LIMIT 10"
            )
            existing_nodes = {row[0] for row in cursor.fetchall()}
            conn.close()

            # Check if old node IDs exist (FIR2 = old 2-node architecture)
            old_ids = {"FIR2"}
            new_ids = {"FLD1", "SLD2", "FIR3", "POL4"}

            if existing_nodes & old_ids:
                logger.warning(
                    f"⚠️  Old database detected with nodes: {existing_nodes}. "
                    f"Migrating to 4-node architecture ({new_ids}). "
                    f"Deleting old database..."
                )
                os.remove(full_path)
                logger.info("✅ Old database removed. Fresh database will be created.")
            else:
                logger.info(f"Database OK — nodes: {existing_nodes or 'empty (first run)'}")

        except Exception as e:
            # If table doesn't exist or any error, just delete
            logger.warning(f"Database check failed ({e}), recreating...")
            try:
                os.remove(full_path)
            except OSError:
                pass


class DisasterSentinel:
    """Main system orchestrator."""

    def __init__(self, config: dict, simulate: bool = False):
        self.config = config
        self.simulate = simulate

        # Initialize subsystems
        logger.info("═" * 55)
        logger.info("  🛡️  DISASTER SENTINEL v2.0 — Initializing")
        logger.info("  4 Nodes · 3-Layer Validation · GRU AI Prediction")
        logger.info("═" * 55)

        # Clean old database if needed (2-node → 4-node migration)
        db_path = config.get("database", {}).get("path", "data/disaster_sentinel.db")
        clean_old_database(db_path)

        # Data store
        self.store = TimeSeriesStore(db_path)

        # Node configs for layer count awareness
        node_configs = config.get("nodes", {})

        # Three-layer validator (with 2-layer support for POL4)
        self.validator = ThreeLayerValidator(
            config.get("three_layer", {}),
            node_configs=node_configs,
        )

        # Risk predictor
        self.risk_predictor = RiskPredictor(config.get("risk_levels", {}), node_configs=node_configs)

        # Alert manager
        alert_cfg = config.get("alerts", {})
        self.alert_manager = AlertManager(alert_cfg.get("sms", {}))

        # SMS
        self.sms = SMSSender(alert_cfg.get("sms", {}))

        # Buzzer & Strobe
        buzzer_cfg = alert_cfg.get("buzzer", {})
        strobe_cfg = alert_cfg.get("strobe", {})
        self.buzzer = BuzzerControl(
            pin=buzzer_cfg.get("gpio_pin", 12),
            enabled=buzzer_cfg.get("enabled", True),
        )
        self.strobe = StrobeControl(
            pin=strobe_cfg.get("gpio_pin", 16),
            enabled=strobe_cfg.get("enabled", True),
        )

        # Wire alert manager to output devices
        self.alert_manager.set_sms_sender(self.sms)
        self.alert_manager.set_buzzer(self.buzzer)
        self.alert_manager.set_strobe(self.strobe)

        # LoRa receiver
        if simulate:
            self.receiver = SimulatedReceiver(config.get("lora", {}))
            logger.info("📡 Using SIMULATED receiver (no hardware)")
        else:
            self.receiver = LoRaReceiver(config.get("lora", {}))
            logger.info("📡 Using REAL LoRa receiver")

        # Dashboard (Port 8080 removed — System uses Central Command Dashboard on Port 5000)
        self.dashboard = None

        # Register packet callback
        self.receiver.on_packet(self.process_packet)

        # Log node summary
        for nid, ncfg in node_configs.items():
            layers = ncfg.get("layer_count", 3)
            hazard = ncfg.get("hazard_type", "?")
            logger.info(f"  📍 {nid}: {ncfg.get('name', nid)} ({hazard}, {layers}-layer)")

    async def process_packet(self, packet: DecodedPacket):
        """
        Main processing pipeline for each received packet.
        
        Flow:
          1. Store in database
          2. Validate 3-layer (or 2-layer) confirmation
          3. Get historical data for trend analysis
          4. Predict risk
          5. Evaluate alerts
        """
        try:
            # 1. Store reading
            await self.store.store_reading(packet)

            # 2. Multi-layer validation (auto-detects 2-layer vs 3-layer)
            validation = self.validator.validate(packet)

            # 3. Get recent history
            history = await self.store.get_recent_readings(packet.node_id, minutes=30)

            # 4. Risk prediction
            risk = self.risk_predictor.predict(
                packet.to_dict(),
                validation,
                history,
            )

            # 5. Alert evaluation
            await self.alert_manager.evaluate(risk, self.store)

        except Exception as e:
            logger.error(f"Processing error: {e}", exc_info=True)

    async def run(self):
        """Start all subsystems."""
        # Initialize database
        await self.store.initialize()

        # Initialize hardware (graceful failure)
        try:
            self.sms.initialize()
        except Exception as e:
            logger.warning(f"SMS init skipped: {e}")

        try:
            self.buzzer.initialize()
        except Exception:
            logger.warning("Buzzer init skipped (no GPIO)")

        try:
            self.strobe.initialize()
        except Exception:
            logger.warning("Strobe init skipped (no GPIO)")

        logger.info("═" * 55)
        logger.info("  🛡️  DISASTER SENTINEL — Running")
        logger.info(f"  Mode: {'SIMULATION' if self.simulate else 'HARDWARE'}")
        logger.info("  Central Command Dashboard: http://localhost:5000")
        logger.info("═" * 55)

        # Run receiver
        await self.receiver.start()

    async def shutdown(self):
        """Graceful shutdown."""
        logger.info("Shutting down...")
        self.receiver.stop()
        await self.buzzer.off()
        await self.strobe.off()
        self.sms.close()
        await self.store.close()
        logger.info("Shutdown complete")


def main():
    parser = argparse.ArgumentParser(description="Disaster Sentinel — Central System")
    parser.add_argument("--simulate", action="store_true",
                        help="Use simulated data (no LoRa hardware needed)")
    parser.add_argument("--config", default="config.yaml",
                        help="Path to configuration file")
    parser.add_argument("--port", type=int, default=None,
                        help="Dashboard port (overrides config)")
    args = parser.parse_args()

    # Load config
    config = load_config(args.config)
    if args.port:
        config.setdefault("dashboard", {})["port"] = args.port

    # Create and run system
    sentinel = DisasterSentinel(config, simulate=args.simulate)

    try:
        asyncio.run(sentinel.run())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        asyncio.run(sentinel.shutdown())


if __name__ == "__main__":
    main()
