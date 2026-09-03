"""
Disaster Sentinel — Alert Manager

Routes alerts to the appropriate channels based on risk level:
  GREEN  → Dashboard normal
  YELLOW → Dashboard warning
  ORANGE → Dashboard alert + Buzzer short beep
  RED    → Dashboard critical + SMS + Buzzer continuous + Strobe
  
Includes cooldown to prevent alert spam.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Callable, Optional

logger = logging.getLogger(__name__)


class AlertManager:
    """Manages alert routing, cooldown, and multi-channel delivery."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self._cooldowns: Dict[str, datetime] = {}
        self._ws_callbacks: List[Callable] = []
        self._sms_sender = None
        self._buzzer = None
        self._strobe = None
        self.cooldown_minutes = self.config.get("cooldown_minutes", 5)
        self.current_states: Dict[str, Dict] = {}

    def set_sms_sender(self, sender):
        """Set SMS sender instance."""
        self._sms_sender = sender

    def set_buzzer(self, buzzer):
        """Set buzzer control instance."""
        self._buzzer = buzzer

    def set_strobe(self, strobe):
        """Set strobe control instance."""
        self._strobe = strobe

    def on_alert(self, callback: Callable):
        """Register WebSocket callback for dashboard updates."""
        self._ws_callbacks.append(callback)

    async def evaluate(self, risk: Dict, store=None):
        """
        Evaluate risk and trigger appropriate alerts.
        
        Args:
            risk: Risk assessment from RiskPredictor
            store: TimeSeriesStore for persisting alerts
        """
        node_id = risk.get("node_id", "")
        risk_level = risk.get("risk_level", "GREEN")
        hazard_name = risk.get("hazard_name", "")

        # Store current state for dashboard
        self.current_states[node_id] = risk

        # Always push to dashboard via WebSocket
        await self._push_dashboard(risk)

        # Determine actions based on risk level
        actions = []

        if risk_level == "RED":
            actions.extend(["dashboard_critical", "sms", "buzzer_continuous", "strobe"])
        elif risk_level == "ORANGE":
            actions.extend(["dashboard_alert", "buzzer_short"])
        elif risk_level == "YELLOW":
            actions.extend(["dashboard_warning"])
        else:
            actions.append("dashboard_normal")
            # Turn off active alarms when back to green
            await self._deactivate_alarms(node_id)

        # Execute actions
        for action in actions:
            await self._execute_action(action, risk, node_id, hazard_name)

        # Store alert if significant
        if risk_level in ("ORANGE", "RED") and store:
            alert_data = {
                "timestamp": datetime.now().isoformat(),
                "node_id": node_id,
                "hazard_name": hazard_name,
                "risk_level": risk_level,
                "probability": risk.get("probability", 0),
                "severity": risk.get("severity", ""),
                "eta_minutes": risk.get("eta_minutes"),
                "confirmation_level": risk.get("confirmation_level", ""),
                "layers_anomalous": risk.get("layers_anomalous", 0),
                "combined_score": risk.get("combined_score", 0),
                "actions_taken": actions,
                "message": self._format_alert_message(risk),
            }
            await store.store_alert(alert_data)

    async def _execute_action(self, action: str, risk: Dict,
                               node_id: str, hazard_name: str):
        """Execute a single alert action."""
        cooldown_key = f"{node_id}:{action}"

        # Check cooldown
        if action in ("sms", "buzzer_continuous") and cooldown_key in self._cooldowns:
            if datetime.now() < self._cooldowns[cooldown_key]:
                return  # Still in cooldown

        if action == "sms" and self._sms_sender:
            message = self._format_sms(risk)
            try:
                await self._sms_sender.send(message)
                self._cooldowns[cooldown_key] = (
                    datetime.now() + timedelta(minutes=self.cooldown_minutes)
                )
                logger.info(f"[Alert] SMS sent for {node_id} {hazard_name}")
            except Exception as e:
                logger.error(f"[Alert] SMS failed: {e}")

        elif action == "buzzer_continuous" and self._buzzer:
            await self._buzzer.continuous_on()
            self._cooldowns[cooldown_key] = (
                datetime.now() + timedelta(minutes=1)
            )

        elif action == "buzzer_short" and self._buzzer:
            await self._buzzer.short_beep()

        elif action == "strobe" and self._strobe:
            await self._strobe.on()

    async def _deactivate_alarms(self, node_id: str):
        """Turn off buzzer and strobe when risk drops."""
        # Only deactivate if no other node is at RED
        any_red = any(
            s.get("risk_level") == "RED"
            for nid, s in self.current_states.items()
            if nid != node_id
        )
        if not any_red:
            if self._buzzer:
                await self._buzzer.off()
            if self._strobe:
                await self._strobe.off()

    async def _push_dashboard(self, risk: Dict):
        """Push update to all WebSocket connections."""
        for cb in self._ws_callbacks:
            try:
                if asyncio.iscoroutinefunction(cb):
                    await cb(risk)
                else:
                    cb(risk)
            except Exception as e:
                logger.error(f"[Alert] WebSocket push failed: {e}")

    def _format_sms(self, risk: Dict) -> str:
        """Format SMS message for emergency alert."""
        return (
            f"🚨 DISASTER SENTINEL ALERT\n\n"
            f"HAZARD: {risk.get('hazard_name', 'UNKNOWN')}\n"
            f"NODE: {risk.get('node_id', '')}\n\n"
            f"Probability: {risk.get('probability_percent', 0)}%\n"
            f"Severity: {risk.get('severity', '')}\n"
            f"Confirmation: {risk.get('confirmation_level', '')} "
            f"({risk.get('layers_anomalous', 0)}/3 layers)\n"
            f"Sustained: {risk.get('sustained_minutes', 0):.0f} min\n"
            f"\n"
            f"ETA to critical: {risk.get('eta_minutes', 'N/A')} min\n"
            f"\n"
            f"Immediate field verification required.\n"
            f"Time: {datetime.now().strftime('%H:%M:%S %d-%b-%Y')}"
        )

    def _format_alert_message(self, risk: Dict) -> str:
        """Format alert message for logging/storage."""
        return (
            f"{risk.get('risk_level', '')} alert for {risk.get('hazard_name', '')} "
            f"at node {risk.get('node_id', '')}: "
            f"probability={risk.get('probability_percent', 0)}%, "
            f"severity={risk.get('severity', '')}, "
            f"confirmation={risk.get('confirmation_level', '')}"
        )

    def get_all_states(self) -> Dict[str, Dict]:
        """Get current risk states for all nodes (for dashboard)."""
        return self.current_states
