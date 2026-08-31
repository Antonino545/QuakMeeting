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

    @unittest.skipIf(sys.platform != "darwin", "macOS specific UI tests")
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

if __name__ == "__main__":
    unittest.main()
