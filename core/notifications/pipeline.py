import logging
from typing import List, Dict, Any
from core.notifications.payload import NotificationPayload
from core.notifications.channels.base_channel import BaseNotificationChannel
from core.notifications.channels.banner_channel import BannerChannel
from core.notifications.channels.webhook_channel import WebhookChannel

logger = logging.getLogger("QuakMeeting.NotificationPipeline")

class NotificationPipelineOrchestrator:
    """Routes events to the appropriate channels based on configuration and context."""
    
    def __init__(self):
        self.channels: List[BaseNotificationChannel] = []
        # By default, we always have the visual banner channel
        self.channels.append(BannerChannel())
        
        # Load webhooks from config later if configured
        self._load_webhooks_from_config()

    def _load_webhooks_from_config(self):
        from core.services.config_service import config_service
        webhooks = config_service.get("webhooks", [])
        for wh in webhooks:
            url = wh.get("url")
            if url:
                allow_private = wh.get("allow_private", False)
                self.channels.append(WebhookChannel(endpoint_url=url, allow_private=allow_private))

    def dispatch(self, payload: NotificationPayload) -> None:
        """Evaluate context (e.g. quiet mode) and route to active channels."""
        
        logger.info(f"Dispatching notification for '{payload.title}' at stage {payload.stage_minutes}m")
        
        # If the user is in Quiet Mode, we modify the payload or suppress channels
        # (For now, the payload inherently carries the is_quiet flag, which the banner channel respects)
        
        for channel in self.channels:
            try:
                channel.send(payload)
            except Exception as e:
                logger.error(f"Error dispatching to {channel.__class__.__name__}: {e}")

# Global orchestrator instance
notification_pipeline = NotificationPipelineOrchestrator()

def _on_reminder_triggered(meeting, stage, **kwargs) -> None:
    from core.notifications.payload import NotificationPayload
    
    # meeting can be a dict or a Meeting object depending on where it's published from (tests vs prod)
    m_dict = meeting.to_dict() if hasattr(meeting, "to_dict") else meeting
    
    # We create the payload mapping
    # target_time_iso is not strictly required if we have raw_meeting_data, but we do our best.
    target_time = getattr(meeting, "start_time", m_dict.get("start_time"))
    
    payload = NotificationPayload(
        event_id=getattr(meeting, "id", m_dict.get("id", "")),
        title=getattr(meeting, "title", m_dict.get("title", "")),
        provider=getattr(meeting, "provider", m_dict.get("provider", "")),
        pilot_type=getattr(meeting, "pilot_type", m_dict.get("pilot_type", "duck")),
        stage_minutes=stage,
        urgency_level="critical" if stage <= 0 else ("high" if stage <= 5 else "normal"),
        target_time=target_time,
        formatted_time_label=f"T-{stage}m",
        action_label=getattr(meeting, "action_btn_text", m_dict.get("action_btn_text", "JOIN")),
        action_url=getattr(meeting, "action_url", m_dict.get("action_url", m_dict.get("meeting_url"))),
        is_quiet=getattr(meeting, "is_quiet_reminder", m_dict.get("is_quiet_reminder", False)),
        is_travel=getattr(meeting, "is_travel", m_dict.get("is_travel", False)),
        raw_meeting_data=m_dict
    )
    notification_pipeline.dispatch(payload)

from core.services.event_bus import event_bus
event_bus.subscribe("REMINDER_TRIGGERED", _on_reminder_triggered)

