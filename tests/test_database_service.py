"""
Unit tests for DatabaseService SQLite storage engine.
"""
import os
import tempfile
import unittest
from datetime import datetime, timezone

from core.services.database_service import DatabaseService


class TestDatabaseService(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_flightdeck.db")
        # Instantiate with isolated path
        self.db = DatabaseService(self.db_path)
        self.db.db_path = self.db_path
        self.db._initialized = False
        self.db.__init__(self.db_path)

    def tearDown(self):
        try:
            if hasattr(self.db._local, "conn") and self.db._local.conn:
                self.db._local.conn.close()
                self.db._local.conn = None
        except Exception:
            pass

    def test_notified_stages_crud_and_pruning(self):
        self.db.record_notified_key("evt1_stage_10")
        self.db.record_notified_key("evt1_stage_0")

        keys = self.db.get_notified_keys()
        self.assertIn("evt1_stage_10", keys)
        self.assertIn("evt1_stage_0", keys)

        self.db.remove_notified_key("evt1_stage_10")
        keys_after = self.db.get_notified_keys()
        self.assertNotIn("evt1_stage_10", keys_after)
        self.assertIn("evt1_stage_0", keys_after)

    def test_banner_history_storage(self):
        row_id = self.db.record_banner_history(
            event_id="evt-zoom",
            title="Sprint Sync",
            stage=10,
            pilot_type="captain",
            provider="Zoom",
            status="sent"
        )
        self.assertGreater(row_id, 0)

        history = self.db.get_banner_history(limit=10)
        self.assertGreaterEqual(len(history), 1)
        self.assertEqual(history[0]["event_id"], "evt-zoom")
        self.assertEqual(history[0]["stage"], 10)
        self.assertEqual(history[0]["pilot_type"], "captain")

    def test_eta_cache_storage_and_expiration(self):
        self.db.set_eta(
            cache_key="route_home_office_transit",
            origin="Home",
            destination="Office",
            mode="transit",
            duration_min=22,
            distance_km=7.5
        )

        eta = self.db.get_eta("route_home_office_transit", max_age_seconds=600)
        self.assertIsNotNone(eta)
        self.assertEqual(eta["duration_minutes"], 22)
        self.assertEqual(eta["distance_km"], 7.5)

        # Expired query
        expired_eta = self.db.get_eta("route_home_office_transit", max_age_seconds=-1)
        self.assertIsNone(expired_eta)

    def test_events_cache_upsert_and_retrieve(self):
        events = [
            {
                "uid": "evt-class-1",
                "title": "Machine Learning",
                "start_time": datetime.now(timezone.utc).isoformat(),
                "location": "Aula 5M",
                "is_travel": False
            }
        ]

        self.db.upsert_events(events)
        cached = self.db.get_cached_events()
        self.assertGreaterEqual(len(cached), 1)
        self.assertEqual(cached[0]["uid"], "evt-class-1")
        self.assertEqual(cached[0]["title"], "Machine Learning")


if __name__ == "__main__":
    unittest.main()
