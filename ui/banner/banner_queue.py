import time
import threading
from typing import Dict, Any, Optional

class BannerQueueItem:
    def __init__(self, meeting_data: Dict[str, Any]):
        self.meeting_data = meeting_data
        self.stage = meeting_data.get("reminder_stage", 0)
        self.is_quiet_reminder = meeting_data.get("is_quiet_reminder", False)
        self.enqueued_at = time.time()

class BannerQueue:
    def __init__(self):
        self._items = []
        self._lock = threading.Lock()

    def push(self, item: BannerQueueItem):
        with self._lock:
            # Deduplicate by meeting id (using title and start time)
            title = item.meeting_data.get("title", "")
            start = str(item.meeting_data.get("start_time", ""))
            m_id = f"{title}_{start}"
            
            # Remove any existing item for this meeting
            self._items = [x for x in self._items if f"{x.meeting_data.get('title', '')}_{x.meeting_data.get('start_time', '')}" != m_id]
            
            self._items.append(item)
            # Priority: stage 0 jumps to front (index 0), otherwise FIFO
            self._items.sort(key=lambda x: (x.stage != 0, x.enqueued_at))

    def pop_next(self) -> Optional[BannerQueueItem]:
        with self._lock:
            now = time.time()
            # Drop items enqueued more than 10 minutes ago
            self._items = [x for x in self._items if (now - x.enqueued_at) <= 600]
            if self._items:
                return self._items.pop(0)
            return None

    def is_empty(self) -> bool:
        with self._lock:
            return len(self._items) == 0

banner_queue = BannerQueue()
