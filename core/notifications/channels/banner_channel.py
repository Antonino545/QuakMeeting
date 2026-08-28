import sys
from core.notifications.payload import NotificationPayload
from core.notifications.channels.base_channel import BaseNotificationChannel

class BannerChannel(BaseNotificationChannel):
    """Dispatches the notification to the visual floating banner."""
    
    def send(self, payload: NotificationPayload) -> bool:
        # We need to construct the legacy dict format for the banner for backwards compatibility
        meeting_data = payload.raw_meeting_data.copy()
        # Add overrides if any from payload processing
        meeting_data["reminder_stage"] = payload.stage_minutes
        
        if sys.platform == "darwin":
            from ui.macos.banner.banner_controller import show_banner_async
            show_banner_async(meeting_data)
        else:
            # We must dispatch via the Qt signal bridge to prevent Wayland crashes
            from core.services.dispatcher import run_on_main_thread_async
            from ui.linux.banner.qt_banner import show_qt_banner
            
            def _launch_qt_banner():
                show_qt_banner(meeting_data)
                
            run_on_main_thread_async(_launch_qt_banner)
            
        return True
