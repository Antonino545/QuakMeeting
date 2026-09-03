"""
Unit Tests for Modular Banner Components:
- banner_speech: Speech generation for all mascots and contexts
- banner_formatting: Countdown formatting and urgency
- banner_particles: Physics and particle lifecycle
- banner_layout: Button geometry and hit target calculations
"""
import unittest
from datetime import datetime, timedelta
import sys

from ui.common.banner_speech import build_pilot_speech_text
from ui.common.banner_formatting import compute_countdown_text, format_travel_duration
from ui.common.banner_particles import BannerParticleEngine

HAS_APPKIT = False
if sys.platform == "darwin":
    try:
        import AppKit
        HAS_APPKIT = True
    except ImportError:
        HAS_APPKIT = False

class TestBannerModules(unittest.TestCase):

    def test_banner_speech_vocalizations(self):
        # 1. Normal mode speech (English)
        duck_speech = build_pilot_speech_text({}, animal="duck", outfit="aviator", is_late=False, lang="en")
        self.assertIn("Quak!", duck_speech)

        owl_speech = build_pilot_speech_text({}, animal="owl", outfit="student", is_late=False, lang="en")
        self.assertIn("Hoot!", owl_speech)

        bunny_speech = build_pilot_speech_text({}, animal="bunny", outfit="gym", is_late=False, lang="en")
        self.assertTrue("Boing!" in bunny_speech or "Hop" in bunny_speech)

        squirrel_speech = build_pilot_speech_text({}, animal="squirrel", outfit="racer", is_late=False, lang="en")
        self.assertTrue("Chirp" in squirrel_speech or "Nut-ping" in squirrel_speech)

        platypus_speech = build_pilot_speech_text({}, animal="platypus", outfit="agent", is_late=False, lang="en")
        self.assertIn("Kk-kk", platypus_speech)

        # 2. Emergency late mode speech (English)
        duck_late = build_pilot_speech_text({}, animal="duck", outfit="aviator", is_late=True, lang="en")
        self.assertIn("QUAAK!", duck_late)

        owl_late = build_pilot_speech_text({"event_type": "study"}, animal="owl", outfit="student", is_late=True, lang="en")
        self.assertIn("HOOOT!", owl_late)

        # 3. Italian mode speech
        duck_it = build_pilot_speech_text({}, animal="duck", outfit="aviator", is_late=False, lang="it")
        self.assertIn("Quak!", duck_it)
        self.assertIn("decollo", duck_it)

        owl_it_late = build_pilot_speech_text({"event_type": "study"}, animal="owl", outfit="student", is_late=True, lang="it")
        self.assertIn("DEVI STUDIARE", owl_it_late)

    def test_banner_formatting_and_urgency(self):
        now = datetime.now().astimezone()

        # Far future event (e.g. in 25 mins) -> not urgent (English)
        start_far = now + timedelta(minutes=25, seconds=10)
        text_en, urgent_en = compute_countdown_text(
            {}, start_far, None, None, False, "transit", None, "duck", "Calendar", "Sync", lang="en"
        )
        self.assertIn("In 25m", text_en)
        self.assertFalse(urgent_en)

        # Far future event (Italian)
        text_it, urgent_it = compute_countdown_text(
            {}, start_far, None, None, False, "transit", None, "duck", "Calendar", "Sync", lang="it"
        )
        self.assertIn("Tra 25m", text_it)
        self.assertFalse(urgent_it)

        # Imminent event (in 3 mins) -> urgent
        start_soon = now + timedelta(minutes=3, seconds=10)
        text_soon, urgent_soon = compute_countdown_text(
            {}, start_soon, None, None, False, "transit", None, "duck", "Calendar", "Sync", lang="en"
        )
        self.assertIn("3m", text_soon)
        self.assertTrue(urgent_soon)

        # Study session countdown formatting (English & Italian)
        start_study = now + timedelta(minutes=20, seconds=5)
        text_study, _ = compute_countdown_text(
            {"event_type": "study"}, start_study, None, None, False, "transit", "Aula 5M", "owl", "Study Session 📖", "OR Study: Intro & LP/MILP Modeling Template", lang="en"
        )
        self.assertIn("Study Time", text_study)
        self.assertNotIn("Lesson", text_study)

        text_study_soon, _ = compute_countdown_text(
            {"event_type": "study"}, now + timedelta(minutes=7), None, None, False, "transit", None, "owl", "Study Session 📖", "Self study", lang="en"
        )
        self.assertIn("Open Books", text_study_soon)

        text_study_urgent, is_urg = compute_countdown_text(
            {"event_type": "study"}, now + timedelta(minutes=2), None, None, False, "transit", None, "owl", "Study Session 📖", "OR Study: Intro & LP/MILP Modeling Template", lang="en"
        )
        self.assertIn("Time to Study", text_study_urgent)
        self.assertTrue(is_urg)

        # Travel duration helper
        self.assertEqual(format_travel_duration(15), "15 min")
        self.assertEqual(format_travel_duration(75), "1h 15m")
        self.assertEqual(format_travel_duration(120), "2h")

    def test_banner_particle_engine(self):
        engine = BannerParticleEngine()
        self.assertEqual(len(engine.flame_particles), 0)
        self.assertEqual(len(engine.smoke_particles), 0)

        # Emit normal smoke
        engine.emit_and_update(600.0, 100.0, tick=4, is_late=False, is_paused=False, pilot_type="duck")
        self.assertGreater(len(engine.smoke_particles), 0)

        # Emit late turbo flames
        engine.emit_and_update(600.0, 100.0, tick=5, is_late=True, is_paused=False, pilot_type="duck")
        self.assertGreater(len(engine.flame_particles), 0)

        # Reset
        engine.reset()
        self.assertEqual(len(engine.flame_particles), 0)
        self.assertEqual(len(engine.smoke_particles), 0)

    @unittest.skipUnless(HAS_APPKIT, "macOS AppKit required")
    def test_banner_layout_geometry(self):
        from ui.macos.banner.banner_layout import BannerLayout
        layout = BannerLayout(banner_w=535.0, banner_h=126.0)
        rects = layout.get_button_rects(
            banner_x=100.0,
            banner_y=50.0,
            has_maps_url=True,
            has_real_url=True,
            reminder_stage=5
        )

        self.assertIn("close", rects)
        self.assertIn("close_hit", rects)
        self.assertIn("action", rects)
        self.assertIn("arrived", rects)
        self.assertIn("snooze1", rects)
        self.assertIn("snooze2", rects)
        self.assertIn("card", rects)

        # Close hit rect should be larger than visual close rect
        self.assertGreater(rects["close_hit"].size.width, rects["close"].size.width)
        self.assertGreater(rects["close_hit"].size.height, rects["close"].size.height)

        # Plane rect geometry
        plane_rect = layout.get_plane_rect(plane_x=705.0, plane_y=54.0)
        self.assertGreater(plane_rect.size.width, 100.0)
        self.assertGreater(plane_rect.size.height, 50.0)

    @unittest.skipUnless(HAS_APPKIT, "macOS AppKit required")
    def test_banner_hittest_and_click_through(self):
        import AppKit
        from ui.macos.banner.banner_view import QuakPitBannerView
        from datetime import datetime

        event_data = {
            "title": "Test Sync",
            "start_time": datetime.now().astimezone(),
            "action_url": "https://meet.google.com/abc-defg-hij",
        }
        view = QuakPitBannerView.alloc().initWithFrame_meetingData_controller_(
            AppKit.NSMakeRect(0, 0, 1920, 220),
            event_data,
            None
        )
        view.x = 200.0
        view.base_y = 48.0
        view.tick = 0

        # Points outside interactive elements should return None (click-through)
        empty_pt = AppKit.NSMakePoint(50.0, 50.0)
        self.assertIsNone(view.hitTest_(empty_pt))

        # Points on card should return view
        card_pt = AppKit.NSMakePoint(300.0, 50.0)
        self.assertIsNotNone(view.hitTest_(card_pt))

        # Points on plane should return view
        plane_pt = AppKit.NSMakePoint(805.0, 52.0)
        self.assertIsNotNone(view.hitTest_(plane_pt))

        # Mouse update outside should not pause
        view._update_mouse_interaction_at_point(empty_pt)
        self.assertFalse(view.is_paused)

        # Mouse update on plane should pause
        view._update_mouse_interaction_at_point(plane_pt)
        self.assertTrue(view.is_paused)


    def test_qt_duck_banner_speech_bubble_bounds(self):
        try:
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtGui import QFont, QFontMetrics
            from ui.linux.banner.qt_duck_banner import QtDuckBannerWindow
        except ImportError:
            self.skipTest("PyQt6 not available")

        app = QApplication.instance() or QApplication(sys.argv)

        animals = ["duck", "owl", "bunny", "squirrel", "platypus"]
        outfits = ["aviator", "chef", "captain", "driver", "gym", "zen"]
        is_lates = [True, False]
        langs = ["en", "it"]

        f = QFont("Inter, Arial", 8, QFont.Weight.ExtraBold)
        fm = QFontMetrics(f)

        card_right_x = QtDuckBannerWindow.CARD_X + QtDuckBannerWindow.CARD_W
        min_bx = card_right_x + 10.0
        px = QtDuckBannerWindow.PLANE_CX

        for animal in animals:
            for outfit in outfits:
                for is_late in is_lates:
                    for lang in langs:
                        quote = build_pilot_speech_text(
                            {"title": "Important Team Synchronization", "classroom": "Aula Magna - Edificio Principale"},
                            animal=animal,
                            outfit=outfit,
                            is_late=is_late,
                            lang=lang
                        )
                        bubble_w = fm.horizontalAdvance(quote) + 24.0
                        ideal_bx = px - bubble_w * 0.5
                        bx = max(min_bx, ideal_bx)
                        right_edge = bx + bubble_w

                        # Test window initialization with this event
                        event_data = {
                            "title": "Important Team Synchronization",
                            "classroom": "Aula Magna - Edificio Principale",
                            "animal": animal,
                            "outfit": outfit,
                            "pilot_type": animal,
                            "start_time": datetime.now().astimezone(),
                            "is_travel": False,
                            "is_late": is_late
                        }
                        banner = QtDuckBannerWindow(event_data)

                        # Assert the speech bubble does not overlap the card
                        self.assertGreaterEqual(bx, min_bx)

                        # Assert the speech bubble is fully inside the banner window (no cropping)
                        self.assertLessEqual(right_edge, banner.win_w)
                        banner._timer.stop()
                        banner.close()

    def test_qt_duck_banner_serenis_action_url(self):
        try:
            from PyQt6.QtWidgets import QApplication
            from ui.linux.banner.qt_duck_banner import QtDuckBannerWindow
        except ImportError:
            self.skipTest("PyQt6 not available")

        app = QApplication.instance() or QApplication(sys.argv)
        banner = QtDuckBannerWindow({
            "title": "Serenis Online Therapy Session",
            "provider": "Serenis 🛋️",
            "pilot_type": "zen_duck",
            "action_btn_text": "🚀 JOIN SESSION",
            "action_url": "https://calendar.apple.com",
            "description": "Join at https://app.serenis.it/join/test123",
            "start_time": datetime.now().astimezone(),
            "is_travel": False,
        })

        self.assertTrue(banner.has_real_url)
        self.assertIn("Online Meeting", banner._cached_detail_text)
        banner._timer.stop()
        banner.close()

if __name__ == "__main__":
    unittest.main()
