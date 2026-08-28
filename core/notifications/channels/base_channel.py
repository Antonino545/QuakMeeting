from abc import ABC, abstractmethod
from core.notifications.payload import NotificationPayload

class BaseNotificationChannel(ABC):
    """Base interface for all notification dispatch channels."""
    
    @abstractmethod
    def send(self, payload: NotificationPayload) -> bool:
        """
        Dispatch the notification.
        Returns True if successful, False otherwise.
        """
        pass
