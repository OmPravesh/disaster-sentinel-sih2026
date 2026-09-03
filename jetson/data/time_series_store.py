"""
Disaster Sentinel — Time-Series Data Store

SQLite-based storage for all sensor readings and processed results.
Provides time-series queries for trend analysis and dashboard display.
"""

import aiosqlite
import logging
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from receiver.packet_decoder import DecodedPacket

logger = logging.getLogger(__name__)


class TimeSeriesStore:
    """Async SQLite time-series store for sensor data."""

    def __init__(self, db_path: str = "data/disaster_sentinel.db"):
        self.db_path = db_path
        self.db: Optional[aiosqlite.Connection] = None

    async def initialize(self):
        """Create database and tables."""
        import os
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        self.db = await aiosqlite.connect(self.db_path)
        self.db.row_factory = aiosqlite.Row

        await self.db.executescript("""
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                node_id TEXT NOT NULL,
                hazard_type INTEGER NOT NULL,
                hazard_name TEXT NOT NULL,
                is_priority INTEGER DEFAULT 0,
                l1_raw REAL,
                l1_anomaly REAL,
                l2_raw REAL,
                l2_anomaly REAL,
                l3_raw REAL,
                l3_anomaly REAL,
                combined_score REAL,
                rate_flag INTEGER,
                rate_name TEXT,
                battery INTEGER,
                seq_num INTEGER,
                rssi INTEGER,
                crc_valid INTEGER DEFAULT 1
            );

            CREATE INDEX IF NOT EXISTS idx_readings_node_time 
                ON sensor_readings(node_id, timestamp);

            CREATE INDEX IF NOT EXISTS idx_readings_hazard_time 
                ON sensor_readings(hazard_name, timestamp);

            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                node_id TEXT NOT NULL,
                hazard_name TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                probability REAL,
                severity TEXT,
                eta_minutes REAL,
                confirmation_level TEXT,
                layers_anomalous INTEGER,
                combined_score REAL,
                actions_taken TEXT,
                message TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_alerts_time 
                ON alerts(timestamp);

            CREATE TABLE IF NOT EXISTS node_status (
                node_id TEXT PRIMARY KEY,
                last_seen TEXT,
                last_battery INTEGER,
                last_rssi INTEGER,
                last_combined_score REAL,
                last_hazard_name TEXT,
                packets_received INTEGER DEFAULT 0,
                is_online INTEGER DEFAULT 0
            );
        """)

        await self.db.commit()
        logger.info(f"Database initialized: {self.db_path}")

    async def store_reading(self, packet: DecodedPacket):
        """Store a decoded packet as a sensor reading."""
        await self.db.execute("""
            INSERT INTO sensor_readings 
            (timestamp, node_id, hazard_type, hazard_name, is_priority,
             l1_raw, l1_anomaly, l2_raw, l2_anomaly, l3_raw, l3_anomaly,
             combined_score, rate_flag, rate_name, battery, seq_num, rssi, crc_valid)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            packet.received_at.isoformat(),
            packet.node_id,
            packet.hazard_type,
            packet.hazard_name,
            1 if packet.is_priority else 0,
            packet.l1_raw, packet.l1_anomaly,
            packet.l2_raw, packet.l2_anomaly,
            packet.l3_raw, packet.l3_anomaly,
            packet.combined_score,
            packet.rate_flag, packet.rate_name,
            packet.battery, packet.seq_num,
            packet.rssi,
            1 if packet.crc_valid else 0,
        ))

        # Update node status
        await self.db.execute("""
            INSERT INTO node_status (node_id, last_seen, last_battery, last_rssi, 
                                      last_combined_score, last_hazard_name, packets_received, is_online)
            VALUES (?, ?, ?, ?, ?, ?, 1, 1)
            ON CONFLICT(node_id) DO UPDATE SET
                last_seen = excluded.last_seen,
                last_battery = excluded.last_battery,
                last_rssi = excluded.last_rssi,
                last_combined_score = excluded.last_combined_score,
                last_hazard_name = excluded.last_hazard_name,
                packets_received = packets_received + 1,
                is_online = 1
        """, (
            packet.node_id,
            packet.received_at.isoformat(),
            packet.battery,
            packet.rssi,
            packet.combined_score,
            packet.hazard_name,
        ))

        await self.db.commit()

    async def get_recent_readings(self, node_id: str, minutes: int = 30) -> List[Dict]:
        """Get recent readings for a node."""
        since = (datetime.now() - timedelta(minutes=minutes)).isoformat()
        cursor = await self.db.execute("""
            SELECT * FROM sensor_readings
            WHERE node_id = ? AND timestamp > ?
            ORDER BY timestamp ASC
        """, (node_id, since))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def get_latest_reading(self, node_id: str) -> Optional[Dict]:
        """Get the most recent reading for a node."""
        cursor = await self.db.execute("""
            SELECT * FROM sensor_readings
            WHERE node_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (node_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_all_latest(self) -> List[Dict]:
        """Get the latest reading for each node."""
        cursor = await self.db.execute("""
            SELECT s.* FROM sensor_readings s
            INNER JOIN (
                SELECT node_id, MAX(timestamp) as max_ts
                FROM sensor_readings
                GROUP BY node_id
            ) latest ON s.node_id = latest.node_id AND s.timestamp = latest.max_ts
            ORDER BY s.node_id
        """)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def get_node_statuses(self) -> List[Dict]:
        """Get status of all registered nodes."""
        cursor = await self.db.execute("""
            SELECT * FROM node_status ORDER BY node_id
        """)
        rows = await cursor.fetchall()

        # Check online status (offline if no packet in 5 minutes)
        cutoff = (datetime.now() - timedelta(minutes=5)).isoformat()
        results = []
        for row in rows:
            d = dict(row)
            d["is_online"] = 1 if d.get("last_seen", "") > cutoff else 0
            results.append(d)
        return results

    async def store_alert(self, alert_data: Dict):
        """Store an alert record."""
        await self.db.execute("""
            INSERT INTO alerts 
            (timestamp, node_id, hazard_name, risk_level, probability,
             severity, eta_minutes, confirmation_level, layers_anomalous,
             combined_score, actions_taken, message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert_data.get("timestamp", datetime.now().isoformat()),
            alert_data.get("node_id", ""),
            alert_data.get("hazard_name", ""),
            alert_data.get("risk_level", ""),
            alert_data.get("probability", 0),
            alert_data.get("severity", ""),
            alert_data.get("eta_minutes"),
            alert_data.get("confirmation_level", ""),
            alert_data.get("layers_anomalous", 0),
            alert_data.get("combined_score", 0),
            json.dumps(alert_data.get("actions_taken", [])),
            alert_data.get("message", ""),
        ))
        await self.db.commit()

    async def get_recent_alerts(self, limit: int = 50) -> List[Dict]:
        """Get recent alerts."""
        cursor = await self.db.execute("""
            SELECT * FROM alerts ORDER BY timestamp DESC LIMIT ?
        """, (limit,))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def get_time_series(self, node_id: str, field: str, minutes: int = 60) -> List[Dict]:
        """Get time-series data for a specific field for charting."""
        since = (datetime.now() - timedelta(minutes=minutes)).isoformat()
        cursor = await self.db.execute(f"""
            SELECT timestamp, {field} as value FROM sensor_readings
            WHERE node_id = ? AND timestamp > ?
            ORDER BY timestamp ASC
        """, (node_id, since))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def close(self):
        """Close database connection."""
        if self.db:
            await self.db.close()
            logger.info("Database connection closed")
