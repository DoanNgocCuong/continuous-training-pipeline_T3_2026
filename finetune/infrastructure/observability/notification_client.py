"""
Notification Client for Slack/Discord webhooks.

Sends pipeline notifications to configured channels.
"""

import os
import json
from typing import Optional
from dataclasses import dataclass
from enum import Enum
import urllib.request
import urllib.error


class NotificationChannel(str, Enum):
    """Notification channel types."""
    SLACK = "slack"
    DISCORD = "discord"


@dataclass
class NotificationMessage:
    """Notification message payload."""
    title: str
    message: str
    channel: NotificationChannel
    severity: str = "info"  # info, warning, error, success
    metadata: Optional[dict] = None


class NotificationClient:
    """Client for sending notifications to Slack/Discord."""

    def __init__(self):
        self.slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
        self.discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")

    def send(self, message: NotificationMessage) -> bool:
        """Send a notification."""
        if message.channel == NotificationChannel.SLACK:
            return self._send_slack(message)
        elif message.channel == NotificationChannel.DISCORD:
            return self._send_discord(message)
        return False

    def _send_slack(self, message: NotificationMessage) -> bool:
        """Send to Slack webhook."""
        if not self.slack_webhook:
            return False

        # Map severity to Slack colors
        color_map = {
            "info": "#36a64f",      # Green
            "success": "#2eb886",   # Bright green
            "warning": "#ff9800",   # Orange
            "error": "#f44336",     # Red
        }

        payload = {
            "attachments": [
                {
                    "color": color_map.get(message.severity, "#36a64f"),
                    "title": message.title,
                    "text": message.message,
                    "fields": self._format_metadata(message.metadata),
                }
            ]
        }

        return self._send_webhook(self.slack_webhook, payload)

    def _send_discord(self, message: NotificationMessage) -> bool:
        """Send to Discord webhook."""
        if not self.discord_webhook:
            return False

        # Map severity to Discord colors (decimal)
        color_map = {
            "info": 3066993,       # Green
            "success": 5763714,    # Bright green
            "warning": 15105570,   # Orange
            "error": 15158332,     # Red
        }

        payload = {
            "embeds": [
                {
                    "title": message.title,
                    "description": message.message,
                    "color": color_map.get(message.severity, 3066993),
                    "fields": self._format_metadata(message.metadata),
                }
            ]
        }

        return self._send_webhook(self.discord_webhook, payload)

    def _format_metadata(self, metadata: Optional[dict]) -> list:
        """Format metadata as Slack/Discord fields."""
        if not metadata:
            return []

        fields = []
        for key, value in metadata.items():
            if isinstance(value, dict):
                value = json.dumps(value)
            fields.append({
                "title": key.replace("_", " ").title(),
                "value": str(value)[:500],  # Limit field length
                "short": True,
            })
        return fields

    def _send_webhook(self, webhook_url: str, payload: dict) -> bool:
        """Send payload to webhook URL."""
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                webhook_url,
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.status == 200
        except (urllib.error.URLError, urllib.error.HTTPError) as e:
            print(f"Failed to send notification: {e}")
            return False

    # Convenience methods

    def notify_pipeline_start(self, version: str, steps: list[str]) -> bool:
        """Notify pipeline started."""
        message = NotificationMessage(
            title=f"🚀 Pipeline Started: {version}",
            message=f"Running steps: {', '.join(steps)}",
            channel=NotificationChannel.SLACK,
            severity="info",
            metadata={"version": version, "steps": steps},
        )
        return self.send(message)

    def notify_pipeline_complete(self, version: str, status: str,
                                  metrics: Optional[dict] = None) -> bool:
        """Notify pipeline completed."""
        message = NotificationMessage(
            title=f"{'✅' if status == 'success' else '❌'} Pipeline Complete: {version}",
            message=f"Status: {status}",
            channel=NotificationChannel.SLACK,
            severity="success" if status == "success" else "error",
            metadata={"version": version, "metrics": metrics},
        )
        return self.send(message)

    def notify_promotion(self, version: str, decision: str,
                         reason: str, metrics: Optional[dict] = None) -> bool:
        """Notify promotion decision."""
        emoji = "🟢" if decision == "promote" else "🔴"
        message = NotificationMessage(
            title=f"{emoji} Promotion Decision: {version}",
            message=f"Decision: {decision}\nReason: {reason}",
            channel=NotificationChannel.SLACK,
            severity="success" if decision == "promote" else "warning",
            metadata={"version": version, "decision": decision, "reason": reason, "metrics": metrics},
        )
        return self.send(message)

    def notify_drift_alert(self, drift_type: str, metric: str,
                           current: float, threshold: float) -> bool:
        """Notify drift alert."""
        message = NotificationMessage(
            title=f"⚠️ Drift Alert: {drift_type}",
            message=f"{metric}: {current:.3f} (threshold: {threshold:.3f})",
            channel=NotificationChannel.SLACK,
            severity="warning",
            metadata={"drift_type": drift_type, "metric": metric, "current": current, "threshold": threshold},
        )
        return self.send(message)


# Singleton instance
_notification_client: Optional[NotificationClient] = None


def get_notification_client() -> NotificationClient:
    """Get the notification client instance."""
    global _notification_client
    if _notification_client is None:
        _notification_client = NotificationClient()
    return _notification_client
