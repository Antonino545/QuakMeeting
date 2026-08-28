import os
import json
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Set

logger = logging.getLogger("QuakMeeting.StateStore")

class NotifiedStateStore:
    def __init__(self, path: str = os.path.expanduser("~/.quakmeeting/notified_stages.json")):
        self.path = path
        self._state = {}
        self._last_write = 0.0

    def load(self) -> Set[str]:
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self._state = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load notified state from {self.path}: {e}")
                self._state = {}

        self.prune()
        return set(self._state.keys())

    def add(self, key: str) -> None:
        now_iso = datetime.now(timezone.utc).isoformat()
        self._state[key] = now_iso

        # Debounce writes to disk
        now_ts = time.time()
        if now_ts - self._last_write >= 1.0:
            self._save()
            self._last_write = now_ts

    def remove(self, key: str) -> None:
        if key in self._state:
            del self._state[key]
            self._save()

    def _save(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            tmp_path = self.path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(self._state, f)
            os.replace(tmp_path, self.path)
        except Exception as e:
            logger.warning(f"Failed to save notified state to {self.path}: {e}")

    def prune(self, max_age_hours: int = 24) -> None:
        now = datetime.now(timezone.utc)
        keys_to_remove = []
        for k, v in self._state.items():
            try:
                dt = datetime.fromisoformat(v)
                if (now - dt) > timedelta(hours=max_age_hours):
                    keys_to_remove.append(k)
            except Exception:
                keys_to_remove.append(k)

        for k in keys_to_remove:
            del self._state[k]

        if keys_to_remove:
            self._save()

    def force_save(self) -> None:
        self._save()
