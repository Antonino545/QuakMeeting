import os
import json
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Set

from core.services.database_service import database_service

logger = logging.getLogger("FlightDeck.StateStore")

class NotifiedStateStore:
    def __init__(self, path: str = os.path.expanduser("~/.flightdeck/notified_stages.json")):
        self.path = path
        self._db = database_service

    def load(self) -> Set[str]:
        keys = self._db.get_notified_keys()
        self.prune()
        logger.debug("Loaded %d notified reminder keys from SQLite.", len(keys))
        return keys

    def add(self, key: str) -> None:
        self._db.record_notified_key(key)
        logger.debug("Recorded notified reminder key in SQLite: %s.", key)

    def remove(self, key: str) -> None:
        self._db.remove_notified_key(key)
        logger.debug("Removed notified reminder key from SQLite: %s.", key)

    def clear(self) -> None:
        self._db.clear_notified_keys()
        logger.debug("Cleared all notified reminder keys from SQLite.")

    @property
    def _state(self) -> "NotifiedStateStore":
        return self

    def prune(self, max_age_hours: int = 24) -> None:
        removed = self._db.prune_notified_keys(max_age_hours=max_age_hours)
        if removed > 0:
            logger.debug("Pruned %d expired reminder keys from SQLite.", removed)

    def force_save(self) -> None:
        pass


class BannerHistoryStore:
    """Persistent storage for all banner notifications sent by FlightDeck via SQLite."""
    def __init__(self, path: str = os.path.expanduser("~/.flightdeck/banner_history.json")):
        self.path = path
        self._db = database_service

    def load(self):
        return self._db.get_banner_history(limit=500)

    def record_banner_sent(self, event_data: dict, stage=None, status: str = "sent") -> dict:
        now_iso = datetime.now(timezone.utc).isoformat()
        start_time_iso = ""
        st = event_data.get("start_time")
        if isinstance(st, datetime):
            start_time_iso = st.isoformat()
        elif st:
            start_time_iso = str(st)

        event_id = str(event_data.get("id") or event_data.get("uid") or "")
        title = str(event_data.get("title") or "Event")
        pilot_type = str(event_data.get("pilot_type") or "duck")
        provider = str(event_data.get("provider") or "")

        self._db.record_banner_history(
            event_id=event_id,
            title=title,
            stage=stage,
            pilot_type=pilot_type,
            provider=provider,
            status=status
        )

        record = {
            "event_id": event_id,
            "title": title,
            "start_time": start_time_iso,
            "stage": stage,
            "pilot_type": pilot_type,
            "provider": provider,
            "sent_at": now_iso,
            "status": status
        }
        logger.debug("Recorded banner history in SQLite: event=%s stage=%s status=%s.", event_id, stage, status)
        return record

    def record_action(self, event_id: str, action: str) -> None:
        pass

    def get_history(self, limit: int = 50):
        return self._db.get_banner_history(limit=limit)


banner_history_store = BannerHistoryStore()

