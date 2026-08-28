from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass(frozen=True)
class NotificationPayload:
    """Immutable payload defining a standardized meeting reminder."""
    event_id: str
    title: str
    provider: str
    pilot_type: str
    stage_minutes: int
    urgency_level: str
    target_time: datetime
    formatted_time_label: str
    action_label: str
    action_url: Optional[str]
    is_quiet: bool
    is_travel: bool
    
    # Raw meeting context for legacy compatibility
    raw_meeting_data: Dict[str, Any]
