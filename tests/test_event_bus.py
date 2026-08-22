import unittest
from core.services.event_bus import EventBus

class TestEventBus(unittest.TestCase):
    def setUp(self):
        self.bus = EventBus()
        self.bus.clear()

    def test_subscribe_and_publish(self):
        received = []
        def on_event(msg):
            received.append(msg)

        self.bus.subscribe("TEST_EVENT", on_event)
        self.bus.publish("TEST_EVENT", msg="hello world")

        self.assertEqual(received, ["hello world"])

    def test_unsubscribe(self):
        received = []
        def on_event(val):
            received.append(val)

        self.bus.subscribe("PULSE", on_event)
        self.bus.publish("PULSE", val=1)
        self.bus.unsubscribe("PULSE", on_event)
        self.bus.publish("PULSE", val=2)

        self.assertEqual(received, [1])

    def test_error_isolation(self):
        def broken_handler():
            raise RuntimeError("Failure in handler")

        received = []
        def good_handler():
            received.append("ok")

        self.bus.subscribe("TEST_ERROR", broken_handler)
        self.bus.subscribe("TEST_ERROR", good_handler)

        # Should not raise exception
        self.bus.publish("TEST_ERROR")
        self.assertEqual(received, ["ok"])

if __name__ == "__main__":
    unittest.main()
