import os
import json
import logging
from typing import List
from core.domain.models import Meeting

logger = logging.getLogger("QuakMeeting.MeetingRepository")

class MeetingRepository:
    """Handles serialization and file I/O for cached meetings."""

    def __init__(self, cache_file: str):
        self.cache_file = cache_file
        self.cache_dir = os.path.dirname(cache_file)

    def save(self, meetings: List[Meeting]) -> None:
        try:
            # Enforce 0700 on the directory
            os.makedirs(self.cache_dir, mode=0o700, exist_ok=True)
            serializable = [m.to_serializable_dict() for m in meetings]
            
            tmp_file = f"{self.cache_file}.tmp"
            
            # Write to tmp file, flush, fsync, and close
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(serializable, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
                
            # Enforce strict 0600 permissions before moving
            os.chmod(tmp_file, 0o600)
            
            # Atomic swap guarantees durability and no torn reads
            os.replace(tmp_file, self.cache_file)
            
        except Exception as e:
            logger.warning(f"Error saving calendar cache to disk: {e}")

    def load(self) -> List[Meeting]:
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return [Meeting.from_dict(item) for item in data]
            except Exception as e:
                logger.warning(f"Error loading calendar cache from disk: {e}")
        return []

    def get_last_modified_time(self) -> float:
        if os.path.exists(self.cache_file):
            return os.path.getmtime(self.cache_file)
        return 0.0
