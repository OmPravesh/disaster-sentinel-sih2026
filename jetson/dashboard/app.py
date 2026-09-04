"""
Disaster Sentinel — Dashboard FastAPI Application

Provides:
  - REST API for node data, alerts, and system status
  - WebSocket for real-time dashboard updates
  - HTML page serving with Jinja2 templates
"""

import asyncio
import json
import logging
from typing import List, Dict
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

logger = logging.getLogger(__name__)


class DashboardApp:
    """Dashboard FastAPI application wrapper."""

    def __init__(self, store, alert_manager, risk_predictor=None, config: dict = None):
        self.store = store
        self.alert_manager = alert_manager
        self.risk_predictor = risk_predictor
        self.config = config or {}
        self.app = FastAPI(title="Disaster Sentinel", version="1.0.0")
        self.active_connections: List[WebSocket] = []

        # Setup routes
        self._setup_routes()

        # Mount static files
        import os
        static_dir = os.path.join(os.path.dirname(__file__), "static")
        template_dir = os.path.join(os.path.dirname(__file__), "templates")
        
        os.makedirs(static_dir, exist_ok=True)
        os.makedirs(template_dir, exist_ok=True)
        os.makedirs(os.path.join(static_dir, "css"), exist_ok=True)
        os.makedirs(os.path.join(static_dir, "js"), exist_ok=True)

        self.app.mount("/static", StaticFiles(directory=static_dir), name="static")
        self.templates = Jinja2Templates(directory=template_dir)

    def _setup_routes(self):
        """Configure all routes."""
        app = self.app

        # =============================================
        # HTML PAGES
        # =============================================

        @app.get("/", response_class=HTMLResponse)
        async def index(request: Request):
            """Main dashboard page."""
            return self.templates.TemplateResponse("index.html", {
                "request": request,
                "title": "Disaster Sentinel",
            })

        @app.get("/alerts", response_class=HTMLResponse)
        async def alerts_page(request: Request):
            """Alert history page."""
            return self.templates.TemplateResponse("alert_history.html", {
                "request": request,
                "title": "Alert History — Disaster Sentinel",
            })

        # =============================================
        # REST API
        # =============================================

        @app.get("/api/status")
        async def get_status():
            """Get overall system status."""
            nodes = await self.store.get_node_statuses()
            online = sum(1 for n in nodes if n.get("is_online"))
            return {
                "system": "Disaster Sentinel",
                "nodes_total": len(nodes),
                "nodes_online": online,
                "nodes": nodes,
                "timestamp": datetime.now().isoformat(),
            }

        @app.get("/api/readings/latest")
        async def get_latest_readings():
            """Get latest reading from each node."""
            readings = await self.store.get_all_latest()
            return {"readings": readings}

        @app.get("/api/readings/{node_id}")
        async def get_node_readings(node_id: str, minutes: int = 30):
            """Get recent readings for a specific node."""
            readings = await self.store.get_recent_readings(node_id, minutes)
            return {"node_id": node_id, "readings": readings}

        @app.get("/api/timeseries/{node_id}/{field}")
        async def get_timeseries(node_id: str, field: str, minutes: int = 60):
            """Get time-series data for charting."""
            allowed_fields = [
                "l1_raw", "l1_anomaly", "l2_raw", "l2_anomaly",
                "l3_raw", "l3_anomaly", "combined_score", "battery"
            ]
            if field not in allowed_fields:
                return {"error": f"Invalid field. Allowed: {allowed_fields}"}
            data = await self.store.get_time_series(node_id, field, minutes)
            return {"node_id": node_id, "field": field, "data": data}

        @app.get("/api/alerts")
        async def get_alerts(limit: int = 50):
            """Get recent alerts."""
            alerts = await self.store.get_recent_alerts(limit)
            return {"alerts": alerts}

        @app.get("/api/risk")
        async def get_risk_states():
            """Get current risk states for all nodes."""
            states = self.alert_manager.get_all_states()
            return {"risk_states": states}

        @app.get("/api/predictions/{node_id}")
        async def get_node_predictions(node_id: str):
            """Get GRU AI future predictions (T+15, T+30, T+60) for a node."""
            history = await self.store.get_recent_readings(node_id, minutes=60)
            if self.risk_predictor:
                preds = self.risk_predictor.predict_future(node_id, history)
            else:
                preds = {
                    "t15": {"probability": 0.0, "severity": "LOW"},
                    "t30": {"probability": 0.0, "severity": "LOW"},
                    "t60": {"probability": 0.0, "severity": "LOW"},
                    "trajectory": "no_predictor",
                    "confidence": 0.0,
                    "model_type": "none",
                }
            return {"node_id": node_id, "predictions": preds}

        @app.get("/api/overview")
        async def get_overview():
            """Get aggregated system overview data for all 4 nodes."""
            nodes = await self.store.get_node_statuses()
            readings = await self.store.get_all_latest()
            alerts = await self.store.get_recent_alerts(limit=5)
            
            # Compute overall risk score (max combined score across nodes)
            max_score = 0.0
            node_overview = []
            for r in readings.values():
                c_score = r.get("combined_score", 0.0)
                if c_score > max_score:
                    max_score = c_score
                node_overview.append(r)
                
            return {
                "overall_risk_score": max_score,
                "overall_risk_percent": round(max_score * 100, 1),
                "nodes": nodes,
                "latest_readings": readings,
                "recent_alerts": alerts,
                "timestamp": datetime.now().isoformat(),
            }

        @app.get("/api/timeseries/{node_id}/layers")
        async def get_layers_timeseries(node_id: str, minutes: int = 60):
            """Get all sensor layer time-series data for a node in a single call."""
            readings = await self.store.get_recent_readings(node_id, minutes)
            timestamps = [r.get("timestamp", "") for r in readings]
            l1_raw = [r.get("l1_raw", 0) for r in readings]
            l1_anomaly = [r.get("l1_anomaly", 0) for r in readings]
            l2_raw = [r.get("l2_raw", 0) for r in readings]
            l2_anomaly = [r.get("l2_anomaly", 0) for r in readings]
            l3_raw = [r.get("l3_raw", 0) for r in readings]
            l3_anomaly = [r.get("l3_anomaly", 0) for r in readings]
            combined = [r.get("combined_score", 0) for r in readings]
            
            return {
                "node_id": node_id,
                "timestamps": timestamps,
                "l1_raw": l1_raw, "l1_anomaly": l1_anomaly,
                "l2_raw": l2_raw, "l2_anomaly": l2_anomaly,
                "l3_raw": l3_raw, "l3_anomaly": l3_anomaly,
                "combined": combined,
            }

        # =============================================
        # WEBSOCKET
        # =============================================

        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket for real-time dashboard updates."""
            await websocket.accept()
            self.active_connections.append(websocket)
            logger.info(f"[WS] Client connected ({len(self.active_connections)} total)")

            try:
                while True:
                    # Keep connection alive, handle client messages
                    data = await websocket.receive_text()
                    # Client can send commands (future: scenario triggers)
                    logger.debug(f"[WS] Received: {data}")
            except WebSocketDisconnect:
                self.active_connections.remove(websocket)
                logger.info(f"[WS] Client disconnected ({len(self.active_connections)} total)")

    async def broadcast(self, data: dict):
        """Broadcast data to all connected WebSocket clients."""
        if not self.active_connections:
            return

        message = json.dumps(data, default=str)
        disconnected = []

        for ws in self.active_connections:
            try:
                await ws.send_text(message)
            except Exception:
                disconnected.append(ws)

        for ws in disconnected:
            self.active_connections.remove(ws)
