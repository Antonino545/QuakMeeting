"""
Unified Notification Provider Architecture for QuakMeeting.

Defines the NotificationProvider protocol and concrete providers:
- MascotBannerProvider: Emits custom animated mascot banner events.
- SystemNotificationProvider: Native OS notification fallback (macOS osascript/AppKit, Linux notify-send, Windows toast).
- SoundNotificationProvider: Plays notification chimes via sound_service.
- CompositeNotificationProvider: Dispatches across multiple providers with fallback support.
- NotificationService: Central facade managing user preferences, history recording, and dispatching.
"""
from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from core.domain.models import Meeting
from core.services.config_service import config_service, ConfigService
from core.services.event_bus import event_bus, EventBus
from core.services.sound_service import play_chime
from core.services.state_store import banner_history_store

logger = logging.getLogger("QuakMeeting.NotificationService")


@dataclass
class ReminderNotification:
    """Unified payload representing a scheduled or imminent reminder notification."""
    id: str
    title: str
    subtitle: str = ""
    body: str = ""
    stage: int = 0
    meeting_id: Optional[str] = None
    meeting: Optional[Meeting] = None
    meeting_dict: Optional[Dict[str, Any]] = None
    action_url: Optional[str] = None
    action_label: Optional[str] = None
    sound_name: Optional[str] = None
    is_quiet: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def from_meeting(cls, meeting: Meeting, stage: int = 0) -> "ReminderNotification":
        """Constructs a ReminderNotification directly from a domain Meeting."""
        m_dict = meeting.to_dict()
        mode_str = (meeting.transport_mode or "transit").capitalize()
        subtitle = meeting.location or (f"{mode_str} to {meeting.location}" if meeting.is_travel else "")
        
        if stage == 0:
            body = "Starting right now!"
        elif stage < 0:
            body = f"Started {abs(stage)}m ago"
        else:
            body = f"Starts in {stage} minutes"

        return cls(
            id=f"{meeting.id}_{stage}_{int(datetime.now(timezone.utc).timestamp())}",
            title=meeting.title,
            subtitle=subtitle,
            body=body,
            stage=stage,
            meeting_id=meeting.id,
            meeting=meeting,
            meeting_dict=m_dict,
            action_url=meeting.meeting_link or meeting.video_link,
            action_label=meeting.action_btn_text or ("Join" if meeting.meeting_link else None),
            sound_name=m_dict.get("sound_name"),
            is_quiet=bool(meeting.is_quiet_reminder),
        )


@runtime_checkable
class NotificationProvider(Protocol):
    """Protocol for delivering reminder notifications to the user."""

    @property
    def name(self) -> str:
        """Name identifying the provider."""
        ...

    def is_available(self) -> bool:
        """Check if this provider can execute in the current environment."""
        ...

    def send(self, notification: ReminderNotification) -> bool:
        """Send a notification. Returns True if sent successfully."""
        ...

    def cancel(self, notification_id: str) -> None:
        """Dismiss or cancel an active notification if supported."""
        ...


class MascotBannerProvider:
    """Delivers notifications using QuakMeeting's custom floating mascot banner."""

    def __init__(self, bus: Optional[EventBus] = None):
        self.bus = bus or event_bus

    @property
    def name(self) -> str:
        return "mascot_banner"

    def is_available(self) -> bool:
        # In test / CI environments, banner bus dispatch is always enabled
        if "unittest" in sys.modules or os.environ.get("CI") or os.environ.get("PYTEST_CURRENT_TEST"):
            return True
        # Mascot banner requires graphical desktop environment (X11, Wayland, macOS, or Windows)
        return bool(
            os.environ.get("DISPLAY")
            or os.environ.get("WAYLAND_DISPLAY")
            or sys.platform == "darwin"
            or sys.platform == "win32"
        )

    def send(self, notification: ReminderNotification) -> bool:
        try:
            m_dict = notification.meeting_dict or {}
            m_dict.setdefault("title", notification.title)
            m_dict.setdefault("reminder_stage", notification.stage)
            m_dict.setdefault("id", notification.meeting_id or notification.id)

            self.bus.publish(
                "REMINDER_TRIGGERED",
                meeting=notification.meeting or notification.meeting_dict,
                stage=notification.stage,
                event_dict=m_dict,
                notification=notification,
            )
            logger.debug(f"[MascotBannerProvider] Dispatched banner for '{notification.title}' (Stage {notification.stage})")
            return True
        except Exception as e:
            logger.error(f"[MascotBannerProvider] Failed to dispatch banner: {e}")
            return False

    def cancel(self, notification_id: str) -> None:
        self.bus.publish("DISMISS_BANNER", notification_id=notification_id)


class SystemNotificationProvider:
    """
    Delivers native operating system desktop notifications.
    macOS: AppleScript osascript display notification
    Linux: notify-send
    Windows: powershell toast / balloon
    """

    @property
    def name(self) -> str:
        return "system_notification"

    def is_available(self) -> bool:
        if sys.platform == "darwin":
            return shutil.which("osascript") is not None
        elif sys.platform.startswith("linux"):
            return shutil.which("notify-send") is not None
        elif sys.platform == "win32":
            return True
        return False

    def send(self, notification: ReminderNotification) -> bool:
        if notification.is_quiet:
            logger.debug("[SystemNotificationProvider] Skipping quiet reminder.")
            return True

        title = notification.title.replace('"', '\\"')
        subtitle = notification.subtitle.replace('"', '\\"')
        body = notification.body.replace('"', '\\"')

        try:
            if sys.platform == "darwin":
                # Use osascript display notification
                script = f'display notification "{body}" with title "{title}"'
                if subtitle:
                    script += f' subtitle "{subtitle}"'
                if notification.sound_name and not notification.is_quiet:
                    script += f' sound name "{notification.sound_name}"'

                res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=3)
                return res.returncode == 0

            elif sys.platform.startswith("linux"):
                cmd = ["notify-send", title, f"{subtitle}\n{body}".strip()]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
                return res.returncode == 0

            elif sys.platform == "win32":
                # PowerShell balloon / toast fallback
                ps_script = f"""
                [reflection.assembly]::loadwithpartialname('System.Windows.Forms') | Out-Null
                $notify = new-object system.windows.forms.notifyicon
                $notify.icon = [system.drawing.systemicons]::information
                $notify.visible = $true
                $notify.showballoontip(5000, '{title}', '{body}', [system.windows.forms.tooltipicon]::None)
                """
                res = subprocess.run(["powershell", "-Command", ps_script], capture_output=True, text=True, timeout=3)
                return res.returncode == 0

        except Exception as e:
            logger.warning(f"[SystemNotificationProvider] Failed to display native notification: {e}")
            return False

        return False

    def cancel(self, notification_id: str) -> None:
        pass


class SoundNotificationProvider:
    """Plays audio notification chimes according to user settings and lesson state."""

    @property
    def name(self) -> str:
        return "sound"

    def is_available(self) -> bool:
        return True

    def send(self, notification: ReminderNotification) -> bool:
        if notification.is_quiet:
            return True
        try:
            play_chime(
                sound_name=notification.sound_name,
                sync=False,
                event_dict=notification.meeting_dict,
            )
            return True
        except Exception as e:
            logger.debug(f"[SoundNotificationProvider] Chime playback error: {e}")
            return False

    def cancel(self, notification_id: str) -> None:
        pass


class CompositeNotificationProvider:
    """Chains multiple notification providers together, with fallback support."""

    def __init__(
        self,
        providers: Optional[List[NotificationProvider]] = None,
        fallback_provider: Optional[NotificationProvider] = None,
    ):
        self.providers: List[NotificationProvider] = providers or []
        self.fallback_provider = fallback_provider

    @property
    def name(self) -> str:
        return "composite"

    def is_available(self) -> bool:
        return any(p.is_available() for p in self.providers) or (
            self.fallback_provider is not None and self.fallback_provider.is_available()
        )

    def send(self, notification: ReminderNotification) -> bool:
        success = False
        dispatched_count = 0

        for provider in self.providers:
            if provider.is_available():
                if provider.send(notification):
                    success = True
                    dispatched_count += 1

        # If all primary providers failed or were unavailable, trigger fallback
        if not success and self.fallback_provider and self.fallback_provider.is_available():
            logger.info(f"[CompositeNotificationProvider] Primary providers unavailable/failed. Invoking fallback: {self.fallback_provider.name}")
            return self.fallback_provider.send(notification)

        return success

    def cancel(self, notification_id: str) -> None:
        for provider in self.providers:
            provider.cancel(notification_id)
        if self.fallback_provider:
            self.fallback_provider.cancel(notification_id)


class NotificationService:
    """
    Central manager for all notification dispatches in QuakMeeting.
    Coordinates MascotBanner, Native System Notifications, and Sounds.
    """

    def __init__(
        self,
        config: Optional[ConfigService] = None,
        bus: Optional[EventBus] = None,
    ):
        self.config = config or config_service
        self.bus = bus or event_bus

        self.mascot_provider = MascotBannerProvider(bus=self.bus)
        self.system_provider = SystemNotificationProvider()
        self.sound_provider = SoundNotificationProvider()

    def notify(self, notification: ReminderNotification) -> bool:
        """
        Dispatches a reminder notification according to current preferences:
        - If mascot banners are enabled (default): show mascot banner.
        - If system notifications are enabled as fallback or alongside: dispatch system notification.
        - Play chime if enabled.
        - Persist to banner history.
        """
        enable_mascot = self.config.get("banner_enabled", True)
        enable_system = self.config.get("system_notifications_enabled", False)
        enable_sound = self.config.get("sound_enabled", True)

        active_providers: List[NotificationProvider] = []
        mascot_active = enable_mascot and self.mascot_provider.is_available()

        if mascot_active:
            active_providers.append(self.mascot_provider)
        elif enable_system and self.system_provider.is_available():
            # Mascot is disabled or unavailable -> fallback directly to OS notification
            active_providers.append(self.system_provider)

        # If user explicitly wants both mascot AND system notification
        if enable_system and mascot_active and self.system_provider.is_available():
            if self.system_provider not in active_providers:
                active_providers.append(self.system_provider)

        # Play chime directly only when mascot banner is not handling it
        if enable_sound and not mascot_active:
            active_providers.append(self.sound_provider)

        composite = CompositeNotificationProvider(
            providers=active_providers,
            fallback_provider=self.system_provider if self.system_provider.is_available() else None,
        )

        sent = composite.send(notification)

        # Record in history store
        if sent and notification.meeting_dict:
            banner_history_store.record_banner_sent(
                notification.meeting_dict,
                stage=notification.stage,
            )

        return sent

    def notify_meeting(self, meeting: Meeting, stage: int = 0) -> bool:
        """Convenience method to notify directly from a Meeting domain object."""
        notification = ReminderNotification.from_meeting(meeting, stage=stage)
        return self.notify(notification)


# Global singleton instance
notification_service = NotificationService()
