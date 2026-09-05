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

from ui.common.banner_speech import build_pilot_speech_text, build_pilot_hover_speech_text
from ui.common.banner_formatting import compute_countdown_text, format_travel_duration
from ui.common.banner_particles import (
    BannerParticleEngine,
    compute_airplane_flight_dynamics,
    compute_towing_cable_hooks
)
from ui.linux.banner.renderers.duck_renderer import QtDuckRenderer

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

        # 4. Advance Flyby mode speech (reminder_stage > 0)
        duck_flyby_en = build_pilot_speech_text({}, animal="duck", outfit="aviator", is_late=False, lang="en", reminder_stage=10)
        self.assertIn("flying by", duck_flyby_en.lower())

        owl_flyby_en = build_pilot_speech_text({}, animal="owl", outfit="student", is_late=False, lang="en", reminder_stage=5)
        self.assertIn("heads up", owl_flyby_en.lower())

        duck_flyby_it = build_pilot_speech_text({}, animal="duck", outfit="aviator", is_late=False, lang="it", reminder_stage=10)
        self.assertIn("al volo", duck_flyby_it.lower())

        owl_flyby_it = build_pilot_speech_text({}, animal="owl", outfit="student", is_late=False, lang="it", reminder_stage=5)
        self.assertIn("al volo", owl_flyby_it.lower())

    def test_pilot_hover_speech_vocalizations(self):
        animals = ["duck", "owl", "bunny", "squirrel", "platypus"]
        for animal in animals:
            quote_en = build_pilot_hover_speech_text(animal=animal, lang="en")
            quote_it = build_pilot_hover_speech_text(animal=animal, lang="it")
            self.assertTrue(len(quote_en) > 0, f"Empty hover quote EN for {animal}")
            self.assertTrue(len(quote_it) > 0, f"Empty hover quote IT for {animal}")

        # Spot check specific mascot vocalizations
        duck_en = build_pilot_hover_speech_text(animal="duck", lang="en")
        self.assertIn("Quak", duck_en)
        self.assertIn("Hover mode", duck_en)

        owl_it = build_pilot_hover_speech_text(animal="owl", lang="it")
        self.assertIn("Uhu", owl_it)
        self.assertIn("Osservo", owl_it)

        bunny_en = build_pilot_hover_speech_text(animal="bunny", lang="en")
        self.assertIn("Hop", bunny_en)
        self.assertIn("Paused", bunny_en)

        squirrel_it = build_pilot_hover_speech_text(animal="squirrel", lang="it")
        self.assertIn("Squit", squirrel_it)

        platypus_en = build_pilot_hover_speech_text(animal="platypus", lang="en")
        self.assertIn("Kk-kk", platypus_en)

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

        # Stage 0 event (< 60s ahead -> "Starting Now!", no seconds)
        start_secs = now + timedelta(seconds=15)
        text_now, urgent_now = compute_countdown_text(
            {}, start_secs, None, None, False, "transit", None, "duck", "Calendar", "Sync", lang="en"
        )
        self.assertEqual(text_now, "⏳ Starting Now!")
        self.assertTrue(urgent_now)

        text_now_it, _ = compute_countdown_text(
            {}, start_secs, None, None, False, "transit", None, "duck", "Calendar", "Sync", lang="it"
        )
        self.assertEqual(text_now_it, "⏳ Inizia ora!")

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
        layout = BannerLayout(banner_w=535.0, banner_h=132.0)
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

    def test_advance_reminder_attributes(self):
        try:
            from PyQt6.QtWidgets import QApplication
            from ui.linux.banner.qt_duck_banner import QtDuckBannerWindow
        except ImportError:
            self.skipTest("PyQt6 not available")

        from core.services.language_service import t

        app = QApplication.instance() or QApplication(sys.argv)

        # Stage 10 (Advance reminder without URL -> Adaptive Slim Height 96px)
        banner_advance = QtDuckBannerWindow({
            "title": "General Sync",
            "provider": "Reminder ⏰",
            "start_time": datetime.now().astimezone() + timedelta(minutes=10),
            "reminder_stage": 10,
            "is_travel": False,
        })
        self.assertEqual(banner_advance.reminder_stage, 10)
        self.assertFalse(banner_advance.has_real_url)
        self.assertTrue(banner_advance.is_slim, "Advance reminder without URL must be slim")
        self.assertEqual(banner_advance.card_h, 96.0, "Slim card height must be 96.0px")
        self.assertIsNotNone(banner_advance._esc_shortcut, "Escape shortcut must be initialized")
        self.assertTrue(len(banner_advance._cached_hover_speech_text) > 0, "Hover speech text must be precomputed")
        self.assertIn("flying by", banner_advance._cached_speech_text.lower())
        rects_adv = banner_advance._get_button_rects(banner_advance.CARD_X, banner_advance.CARD_Y)
        self.assertEqual(rects_adv["action"].width(), 0.0, "No action button on non-URL advance reminder")
        self.assertEqual(rects_adv["snooze1"].width(), 0.0, "No snooze button on advance reminder (Option A)")
        self.assertEqual(rects_adv["snooze2"].width(), 0.0, "No skip button on advance reminder (Option A)")
        banner_advance._timer.stop()
        banner_advance.close()

        # Advance reminder WITH real URL retains Join button only (standard 132px height)
        banner_advance_url = QtDuckBannerWindow({
            "title": "Strategy Call",
            "provider": "Google Meet 🎥",
            "action_url": "https://meet.google.com/abc-defg-hij",
            "start_time": datetime.now().astimezone() + timedelta(minutes=10),
            "reminder_stage": 10,
            "is_travel": False,
        })
        self.assertTrue(banner_advance_url.has_real_url)
        self.assertFalse(banner_advance_url.is_slim, "Advance reminder with URL must not be slim")
        self.assertEqual(banner_advance_url.card_h, 132.0, "Standard card height must be 132.0px")
        rects_adv_url = banner_advance_url._get_button_rects(banner_advance_url.CARD_X, banner_advance_url.CARD_Y)
        self.assertEqual(rects_adv_url["action"].width(), 220.0, "Meeting advance reminder retains [🚀 Join Meeting]")
        self.assertEqual(rects_adv_url["snooze1"].width(), 0.0, "No snooze button on meeting advance reminder")
        self.assertEqual(rects_adv_url["snooze2"].width(), 0.0, "No skip button on meeting advance reminder")
        # Check vertical breathing room between subtitle and button
        sub_bottom = banner_advance_url.CARD_Y + 58.0 + 18.0
        self.assertGreaterEqual(rects_adv_url["action"].y() - sub_bottom, 8.0, "Must have >= 8px space below time subtitle")
        banner_advance_url._timer.stop()
        banner_advance_url.close()

        # Stage 0 (Event-time reminder -> standard 132px height)
        banner_zero = QtDuckBannerWindow({
            "title": "General Sync",
            "provider": "Reminder ⏰",
            "start_time": datetime.now().astimezone(),
            "reminder_stage": 0,
            "is_travel": False,
        })
        self.assertEqual(banner_zero.reminder_stage, 0)
        self.assertFalse(banner_zero.has_real_url)
        self.assertFalse(banner_zero.is_slim, "Stage 0 reminder must not be slim")
        self.assertEqual(banner_zero.card_h, 132.0, "Stage 0 card height must be 132.0px")
        self.assertNotIn("flying by", banner_zero._cached_speech_text.lower())
        rects_zero = banner_zero._get_button_rects(banner_zero.CARD_X, banner_zero.CARD_Y)
        self.assertEqual(rects_zero["action"].width(), 220.0)
        self.assertEqual(rects_zero["snooze1"].width(), 0.0)
        banner_zero._timer.stop()
        banner_zero.close()

        # Stage 0 WITH real URL has Join button only (Option A - minimalist, no redundant Got it)
        banner_zero_url = QtDuckBannerWindow({
            "title": "Strategy Call",
            "provider": "Google Meet 🎥",
            "action_url": "https://meet.google.com/abc-defg-hij",
            "start_time": datetime.now().astimezone(),
            "reminder_stage": 0,
            "is_travel": False,
        })
        self.assertFalse(banner_zero_url.is_slim, "Stage 0 reminder with URL must not be slim")
        self.assertEqual(banner_zero_url.card_h, 132.0, "Stage 0 card height must be 132.0px")
        rects_zero_url = banner_zero_url._get_button_rects(banner_zero_url.CARD_X, banner_zero_url.CARD_Y)
        self.assertEqual(rects_zero_url["action"].width(), 220.0, "Single prominent Join action button")
        self.assertEqual(rects_zero_url["snooze1"].width(), 0.0, "No redundant Got it button")
        banner_zero_url._timer.stop()
        banner_zero_url.close()

        # Travel / Maps in-person events: Directions + Arrived button with responsive widths
        banner_travel_adv = QtDuckBannerWindow({
            "title": "Dentist Appointment",
            "provider": "Google Calendar",
            "start_time": datetime.now().astimezone() + timedelta(minutes=15),
            "location": "Piazza Duomo 1, Milano",
            "travel_time_minutes": 25,
            "transport_mode": "transit",
            "is_travel": True,
            "maps_url": "https://maps.google.com/?q=Piazza+Duomo+1",
            "reminder_stage": 15,
        })
        self.assertTrue(banner_travel_adv.has_maps_url)
        rects_tr_adv = banner_travel_adv._get_button_rects(banner_travel_adv.CARD_X, banner_travel_adv.CARD_Y)
        self.assertEqual(rects_tr_adv["action"].width(), 260.0, "Advance travel reminder has 260px Directions button")
        self.assertEqual(rects_tr_adv["arrived"].width(), 227.0, "Advance travel reminder has 227px Arrived button")
        sub_bottom_tr = banner_travel_adv.CARD_Y + 58.0 + 18.0
        self.assertGreaterEqual(rects_tr_adv["arrived"].y() - sub_bottom_tr, 8.0, "Must have >= 8px space below time subtitle")
        banner_travel_adv._timer.stop()
        banner_travel_adv.close()

        # Advance travel reminder without URL (only [📍 I'm Here] 200px)
        banner_travel_nourl = QtDuckBannerWindow({
            "title": "Office Walk",
            "provider": "Reminder ⏰",
            "start_time": datetime.now().astimezone() + timedelta(minutes=15),
            "location": "Building B",
            "is_travel": True,
            "reminder_stage": 15,
        })
        rects_tr_no = banner_travel_nourl._get_button_rects(banner_travel_nourl.CARD_X, banner_travel_nourl.CARD_Y)
        self.assertEqual(rects_tr_no["action"].width(), 0.0)
        self.assertEqual(rects_tr_no["arrived"].width(), 200.0, "No-URL travel reminder has 200px Arrived button")
        banner_travel_nourl._timer.stop()
        banner_travel_nourl.close()

        # Stage 0 Travel with Maps and Real URL (2 buttons: Action + I'm Here, Got it removed as redundant)
        banner_stage0_2btn = QtDuckBannerWindow({
            "title": "Hybrid Meeting",
            "provider": "Google Calendar",
            "start_time": datetime.now().astimezone(),
            "location": "Via Roma 10",
            "is_travel": True,
            "maps_url": "https://maps.google.com/?q=Via+Roma+10",
            "action_url": "https://meet.google.com/xyz",
            "reminder_stage": 0,
        })
        rects_2btn = banner_stage0_2btn._get_button_rects(banner_stage0_2btn.CARD_X, banner_stage0_2btn.CARD_Y)
        self.assertEqual(rects_2btn["action"].width(), 260.0, "Primary action button is 260px wide")
        self.assertEqual(rects_2btn["arrived"].width(), 227.0, "I'm Here button is 227px wide")
        self.assertEqual(rects_2btn["snooze1"].width(), 0.0, "Got it button is removed when Join and I'm Here are present")
        banner_stage0_2btn._timer.stop()
        banner_stage0_2btn.close()

        # Translations exist
        self.assertEqual(t("banner_heads_up", lang="en"), "👀 Heads Up")
        self.assertEqual(t("banner_heads_up", lang="it"), "👀 Preavviso")
        self.assertEqual(t("banner_flyby_pill", lang="en"), "✈️ FLYBY")
        self.assertEqual(t("banner_flyby_pill", lang="it"), "✈️ AL VOLO")
        self.assertEqual(t("banner_im_here", lang="en"), "📍 I'm Here")
        self.assertEqual(t("banner_im_here", lang="it"), "📍 Sono qui")

    def test_mascot_blinking_cycle(self):
        renderer = QtDuckRenderer()
        # Non-blinking ticks (eyes open during entry and level flight)
        self.assertFalse(renderer.is_eye_blinking(0))
        self.assertFalse(renderer.is_eye_blinking(50))
        self.assertFalse(renderer.is_eye_blinking(123))
        # Natural blink window (tick % 130 >= 124)
        self.assertTrue(renderer.is_eye_blinking(124))
        self.assertTrue(renderer.is_eye_blinking(125))
        self.assertTrue(renderer.is_eye_blinking(129))
        # Blink window ends and eyes reopen
        self.assertFalse(renderer.is_eye_blinking(130))
        # Next blink cycle
        self.assertFalse(renderer.is_eye_blinking(253))
        self.assertTrue(renderer.is_eye_blinking(254))

    def test_airplane_flight_dynamics(self):
        # 1. Paused mode: subtle hovering breathing oscillations
        fx_p, fy_p, pitch_p = compute_airplane_flight_dynamics(tick=10, is_paused=True)
        self.assertIsInstance(fx_p, float)
        self.assertIsInstance(fy_p, float)
        self.assertIsInstance(pitch_p, float)
        self.assertLess(abs(pitch_p), 2.0, "Hover pitch must remain subtle (< 2 deg)")

        # 2. Flying mode: dynamic engine thrust, aerodynamic lift, and pitch
        fx_f, fy_f, pitch_f = compute_airplane_flight_dynamics(tick=0, is_paused=False)
        self.assertIsInstance(fx_f, float)
        self.assertIsInstance(fy_f, float)
        self.assertIsInstance(pitch_f, float)
        # At tick=0, cos(0) = 1.0, pitch should have positive dive tendency (+4.2)
        self.assertGreater(pitch_f, 3.5)

        # Dynamic variation across flight frames
        _, _, pitch_climb = compute_airplane_flight_dynamics(tick=83, is_paused=False)
        # math.cos(83 * 0.038) is close to -1.0 (climb angle)
        self.assertLess(pitch_climb, -2.0, "Pitch should climb (negative angle) during ascent")

    def test_towing_cable_hooks_geometry(self):
        px, py = 600.0, 100.0

        # Qt Coordinates (+Y is down)
        (top_qt, bot_qt) = compute_towing_cable_hooks(px, py, pitch_deg=0.0, is_qt_coords=True)
        self.assertAlmostEqual(top_qt[0], px - 36.0, delta=0.01)
        self.assertAlmostEqual(top_qt[1], py - 4.0, delta=0.01) # Top is smaller Y
        self.assertAlmostEqual(bot_qt[0], px - 36.0, delta=0.01)
        self.assertAlmostEqual(bot_qt[1], py + 4.0, delta=0.01) # Bottom is larger Y

        # Cocoa Coordinates (+Y is up)
        (top_cocoa, bot_cocoa) = compute_towing_cable_hooks(px, py, pitch_deg=0.0, is_qt_coords=False)
        self.assertAlmostEqual(top_cocoa[0], px - 36.0, delta=0.01)
        self.assertAlmostEqual(top_cocoa[1], py + 4.0, delta=0.01) # Top is larger Y
        self.assertAlmostEqual(bot_cocoa[0], px - 36.0, delta=0.01)
        self.assertAlmostEqual(bot_cocoa[1], py - 4.0, delta=0.01) # Bottom is smaller Y

        # Pitch rotation tests: when pitch rotates, hooks rotate around (px, py)
        (top_rot, bot_rot) = compute_towing_cable_hooks(px, py, pitch_deg=10.0, is_qt_coords=True)
        self.assertNotEqual(top_rot[0], px - 36.0)
        self.assertNotEqual(top_rot[1], py - 4.0)

    def test_qt_banner_dynamic_airplane_state(self):
        try:
            from PyQt6.QtWidgets import QApplication
            from ui.linux.banner.qt_duck_banner import QtDuckBannerWindow
        except ImportError:
            self.skipTest("PyQt6 not available")
        app = QApplication.instance() or QApplication(sys.argv)
        banner = QtDuckBannerWindow({
            "title": "Sync Meeting",
            "provider": "Google Meet",
            "start_time": datetime.now().astimezone(),
        })
        p0_x, p0_y, pitch0 = banner._get_airplane_dynamics()
        banner.tick = 40
        p1_x, p1_y, pitch1 = banner._get_airplane_dynamics()
        self.assertNotEqual((p0_x, p0_y), (p1_x, p1_y), "Airplane must dynamically float across ticks")
        self.assertNotEqual(pitch0, pitch1, "Airplane pitch angle must dynamically change across ticks")
        # Step animation tick to test hover check, physics, and particle simulation without error
        banner._step()
        banner._timer.stop()
        banner.close()

if __name__ == "__main__":
    unittest.main()

