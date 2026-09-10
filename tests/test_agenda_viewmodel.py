import unittest
from datetime import datetime, timedelta, timezone

from core.domain.clock import FakeClock
from core.domain.models import CalendarEvent, Meeting, EventCategory
from core.domain.state_machine import EventState
from ui.common.agenda_viewmodel import AgendaViewModel, AgendaEventVM


class TestAgendaViewModel(unittest.TestCase):
    def test_build_event_vm(self):
        clock = FakeClock(datetime(2026, 9, 10, 9, 0, 0, tzinfo=timezone.utc))

        event = CalendarEvent(
            uid="evt-101",
            title="Satellite Communications",
            start_time=datetime(2026, 9, 10, 10, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 9, 10, 11, 30, 0, tzinfo=timezone.utc),
            classroom="Aula 5M",
            teacher="Prof. Rossi",
            location="Politecnico",
            category=EventCategory.CLASS.value,
            pilot_type="owl"
        )

        vm = AgendaViewModel.build_event_vm(event, clock=clock)

        self.assertEqual(vm.uid, "evt-101")
        self.assertEqual(vm.title, "Satellite Communications")
        self.assertIn("Aula 5M", vm.subtitle)
        self.assertIn("Prof. Rossi", vm.subtitle)
        self.assertEqual(vm.icon, "🎓")
        self.assertEqual(vm.state, EventState.UPCOMING)
        self.assertTrue(vm.capabilities.has_location)
        self.assertFalse(vm.capabilities.can_join)

    def test_arrived_and_in_call_badges(self):
        clock = FakeClock(datetime(2026, 9, 10, 14, 0, 0, tzinfo=timezone.utc))

        event = CalendarEvent(
            uid="evt-zoom",
            title="Weekly Sprint Planning",
            start_time=datetime(2026, 9, 10, 14, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 9, 10, 15, 0, 0, tzinfo=timezone.utc),
            meeting_url="https://zoom.us/j/999",
            is_arrived=True,
            arrival_reason="call:Zoom",
            category=EventCategory.VIDEO_MEETING.value
        )

        vm = AgendaViewModel.build_event_vm(event, clock=clock)

        self.assertTrue(vm.capabilities.can_join)
        self.assertTrue(vm.capabilities.show_arrival_badge)
        self.assertTrue(vm.capabilities.show_in_call_badge)
        self.assertIn("Zoom", vm.badge_text)

    def test_build_list_filters_today(self):
        clock = FakeClock(datetime(2026, 9, 10, 8, 0, 0, tzinfo=timezone.utc))

        today_event = CalendarEvent(
            uid="evt-today",
            title="Today Meeting",
            start_time=datetime(2026, 9, 10, 11, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 9, 10, 12, 0, 0, tzinfo=timezone.utc),
        )
        tomorrow_event = CalendarEvent(
            uid="evt-tomorrow",
            title="Tomorrow Meeting",
            start_time=datetime(2026, 9, 11, 11, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 9, 11, 12, 0, 0, tzinfo=timezone.utc),
        )

        vms = AgendaViewModel.build([today_event, tomorrow_event], clock=clock)
        self.assertEqual(len(vms), 1)
        self.assertEqual(vms[0].uid, "evt-today")

    def test_navigation_action_and_maps_fallback(self):
        clock = FakeClock(datetime(2026, 9, 10, 8, 0, 0, tzinfo=timezone.utc))

        event = CalendarEvent(
            uid="evt-loc",
            title="Dentist Appointment",
            start_time=datetime(2026, 9, 10, 15, 0, 0, tzinfo=timezone.utc),
            location="Corso Francia 20, Torino",
            travel_time_minutes=25,
            is_travel=True
        )

        vm = AgendaViewModel.build_event_vm(event, clock=clock)
        self.assertTrue(vm.has_action)
        self.assertTrue(vm.capabilities.can_navigate)
        self.assertFalse(vm.capabilities.can_join)
        self.assertIn("25m", vm.action_btn_text)
        self.assertIn("Corso%20Francia", vm.action_url)

    def test_dict_compatibility(self):
        clock = FakeClock(datetime(2026, 9, 10, 8, 0, 0, tzinfo=timezone.utc))

        raw_dict = {
            "id": "dict-1",
            "title": "Dict Event",
            "start_time": datetime(2026, 9, 10, 16, 0, 0, tzinfo=timezone.utc),
            "meeting_url": "https://meet.google.com/abc-defg-hij",
            "pilot_type": "captain"
        }

        vm = AgendaViewModel.build_event_vm(raw_dict, clock=clock)
        self.assertEqual(vm.uid, "dict-1")
        self.assertEqual(vm.icon, "✈️")
        self.assertTrue(vm.capabilities.can_join)
        self.assertTrue(vm.has_action)


if __name__ == "__main__":
    unittest.main()

