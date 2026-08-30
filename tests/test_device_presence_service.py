"""
Unit tests for DevicePresenceService (HTTP Server & Device Sync).
"""
import unittest
import urllib.request
import urllib.parse
import json
import time
from core.domain.models import DeviceActivity
from core.services.device_presence_service import DevicePresenceService, get_local_ip
from core.services.event_bus import EventBus
from core.services.config_service import ConfigService


class TestDevicePresenceService(unittest.TestCase):
    def setUp(self):
        self.bus = EventBus()
        self.config = ConfigService()
        self.service = DevicePresenceService()
        self.service.bus = self.bus
        self.service.config = self.config
        self.port = 8789
        self.service.start(port=self.port)
        time.sleep(0.1)

    def tearDown(self):
        self.service.stop()
        time.sleep(0.05)

    def test_local_ip_detection(self):
        ip = get_local_ip()
        self.assertIsInstance(ip, str)
        self.assertTrue(len(ip) >= 7)  # e.g. 127.0.0.1 or 192.168.x.x

    def test_health_endpoint(self):
        url = f"http://127.0.0.1:{self.port}/health"
        req = urllib.request.urlopen(url)
        self.assertEqual(req.getcode(), 200)
        data = json.loads(req.read().decode("utf-8"))
        self.assertEqual(data.get("status"), "healthy")

    def test_activity_endpoint_get(self):
        received_events = []
        self.bus.subscribe("DEVICE_ACTIVITY_RECEIVED", lambda **kwargs: received_events.append(kwargs))

        url = f"http://127.0.0.1:{self.port}/api/activity?device=ipad&state=studying&app=GoodNotes"
        req = urllib.request.urlopen(url)
        self.assertEqual(req.getcode(), 200)
        data = json.loads(req.read().decode("utf-8"))
        self.assertTrue(data.get("success"))

        self.assertEqual(len(received_events), 1)
        self.assertEqual(received_events[0].get("device_type"), "ipad")
        self.assertEqual(received_events[0].get("state"), "studying")
        self.assertEqual(received_events[0].get("app_name"), "GoodNotes")

        # Verify registered devices
        state = self.service.get_device_state("ipad")
        self.assertIsNotNone(state)
        self.assertEqual(state.get("state"), "studying")
        self.assertEqual(state.get("app_name"), "GoodNotes")

    def test_activity_endpoint_post_json(self):
        received_events = []
        self.bus.subscribe("DEVICE_ACTIVITY_RECEIVED", lambda **kwargs: received_events.append(kwargs))

        url = f"http://127.0.0.1:{self.port}/api/activity"
        payload = json.dumps({
            "device": "iphone",
            "state": "distracted",
            "app": "TikTok"
        }).encode("utf-8")

        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(req)
        self.assertEqual(resp.getcode(), 200)

        self.assertEqual(len(received_events), 1)
        self.assertEqual(received_events[0].get("device_type"), "iphone")
        self.assertEqual(received_events[0].get("state"), "distracted")
        self.assertEqual(received_events[0].get("app_name"), "TikTok")

    def test_status_endpoint(self):
        # Record an activity first
        act = DeviceActivity(device_type="ipad", state="studying", app_name="Notability")
        self.service.record_activity(act)

        url = f"http://127.0.0.1:{self.port}/api/status"
        req = urllib.request.urlopen(url)
        self.assertEqual(req.getcode(), 200)
        data = json.loads(req.read().decode("utf-8"))
        self.assertEqual(data.get("status"), "online")
        self.assertIn("ipad", data.get("registered_devices", {}))

    def test_setup_page_html(self):
        url = f"http://127.0.0.1:{self.port}/setup"
        req = urllib.request.urlopen(url)
        self.assertEqual(req.getcode(), 200)
        html = req.read().decode("utf-8")
        self.assertIn("QuakMeeting Device Sync", html)
        self.assertIn("Simulate iPad Study Heartbeat", html)
        self.assertIn("Simulate iPhone Distraction", html)


if __name__ == "__main__":
    unittest.main()
