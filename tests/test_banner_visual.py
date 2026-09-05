"""
Visual Snapshot Test for QuakMeeting Banners.
Renders both the Advance Flyby Reminder (stage > 0) and the Event-Time Looping Banner (stage 0),
asserts visual differentiation, and saves snapshot images to artifacts for visual verification.
"""
import os
import sys
import unittest
from datetime import datetime, timedelta

# Set offscreen platform for headless Qt rendering
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QImage, QPainter, QColor, QFont

from ui.linux.banner.qt_duck_banner import QtDuckBannerWindow

ARTIFACTS_DIR = "/home/antonino54/.gemini/antigravity/brain/168cb871-30be-4d6b-a28d-b3dce1b10c61"

class TestBannerVisualSnapshots(unittest.TestCase):

    def setUp(self):
        self.app = QApplication.instance() or QApplication(sys.argv)

    def test_render_and_compare_banners(self):
        now = datetime.now().astimezone()

        # 1. Advance Flyby Banner (Stage 10)
        event_advance = {
            "title": "Strategy & Roadmap Planning",
            "provider": "Reminder ⏰",
            "start_time": now + timedelta(minutes=10),
            "reminder_stage": 10,
            "is_travel": False,
            "pilot_type": "duck",
            "animal": "duck",
            "outfit": "aviator",
        }
        banner_advance = QtDuckBannerWindow(event_advance)
        banner_advance.resize(int(banner_advance.win_w), int(banner_advance.win_h))
        banner_advance.win_x = 0
        banner_advance.tick = 30
        banner_advance._update_countdown_text()

        img_advance = QImage(int(banner_advance.win_w), int(banner_advance.win_h), QImage.Format.Format_ARGB32_Premultiplied)
        img_advance.fill(QColor(0, 0, 0, 0))
        p_adv = QPainter(img_advance)
        banner_advance.render(p_adv)
        p_adv.end()

        advance_path = os.path.join(ARTIFACTS_DIR, "advance_flyby_banner.png")
        img_advance.save(advance_path)
        self.assertTrue(os.path.exists(advance_path))
        self.assertGreater(os.path.getsize(advance_path), 1000)
        self.assertTrue(banner_advance.is_slim, "Advance non-URL reminder must be slim")
        self.assertEqual(banner_advance.card_h, 96.0, "Slim card height must be 96.0px")
        rects_adv = banner_advance._get_button_rects(banner_advance.CARD_X, banner_advance.CARD_Y)
        self.assertEqual(rects_adv["action"].width(), 0.0, "Advance non-URL reminder should have no primary button")
        self.assertEqual(rects_adv["snooze1"].width(), 0.0, "Advance reminder has no snooze button (Option A)")
        self.assertEqual(rects_adv["snooze2"].width(), 0.0, "Advance reminder has no skip button (Option A)")

        banner_advance._timer.stop()
        banner_advance.close()

        # 2. Advance Online Meeting Banner (Stage 10 - With video link)
        event_meeting = {
            "title": "Quarterly Product Review",
            "provider": "Google Meet 🎥",
            "action_url": "https://meet.google.com/abc-defg-hij",
            "start_time": now + timedelta(minutes=10),
            "reminder_stage": 10,
            "is_travel": False,
            "pilot_type": "captain",
            "animal": "duck",
            "outfit": "captain",
        }
        banner_meeting = QtDuckBannerWindow(event_meeting)
        banner_meeting.resize(int(banner_meeting.win_w), int(banner_meeting.win_h))
        banner_meeting.win_x = 0
        banner_meeting.tick = 30
        banner_meeting._update_countdown_text()

        img_meeting = QImage(int(banner_meeting.win_w), int(banner_meeting.win_h), QImage.Format.Format_ARGB32_Premultiplied)
        img_meeting.fill(QColor(0, 0, 0, 0))
        p_meet = QPainter(img_meeting)
        banner_meeting.render(p_meet)
        p_meet.end()

        self.assertFalse(banner_meeting.is_slim, "Meeting banner with URL retains standard height")
        self.assertEqual(banner_meeting.card_h, 126.0, "Standard card height is 126.0px")
        rects_meet = banner_meeting._get_button_rects(banner_meeting.CARD_X, banner_meeting.CARD_Y)
        self.assertEqual(rects_meet["action"].width(), 220.0, "Meeting advance reminder retains [🚀 Join Meeting]")
        self.assertEqual(rects_meet["snooze1"].width(), 0.0, "No snooze button on meeting advance reminder")
        self.assertEqual(rects_meet["snooze2"].width(), 0.0, "No skip button on meeting advance reminder")

        banner_meeting._timer.stop()
        banner_meeting.close()

        # 3. Stage 0 Looping Banner (Stage 0 - Exactly at start time)
        event_zero = {
            "title": "Strategy & Roadmap Planning",
            "provider": "Reminder ⏰",
            "start_time": now + timedelta(seconds=15),
            "reminder_stage": 0,
            "is_travel": False,
            "pilot_type": "duck",
            "animal": "duck",
            "outfit": "aviator",
        }
        banner_zero = QtDuckBannerWindow(event_zero)
        banner_zero.resize(int(banner_zero.win_w), int(banner_zero.win_h))
        banner_zero.win_x = 0
        banner_zero.tick = 30
        banner_zero._update_countdown_text()

        img_zero = QImage(int(banner_zero.win_w), int(banner_zero.win_h), QImage.Format.Format_ARGB32_Premultiplied)
        img_zero.fill(QColor(0, 0, 0, 0))
        p_zero = QPainter(img_zero)
        banner_zero.render(p_zero)
        p_zero.end()

        zero_path = os.path.join(ARTIFACTS_DIR, "stage0_event_banner.png")
        img_zero.save(zero_path)
        self.assertTrue(os.path.exists(zero_path))
        self.assertGreater(os.path.getsize(zero_path), 1000)

        self.assertFalse(banner_zero.is_slim)
        self.assertEqual(banner_zero.card_h, 126.0)
        rects_zero = banner_zero._get_button_rects(banner_zero.CARD_X, banner_zero.CARD_Y)
        self.assertEqual(rects_zero["action"].width(), 220.0, "Stage 0 banner must have 'Got it' primary button")
        self.assertEqual(rects_zero["snooze1"].width(), 0.0, "Stage 0 non-URL reminder uses action button as Got it")

        banner_zero._timer.stop()
        banner_zero.close()

        # 4. Mascot Hover Reaction (Hovering airplane -> playful quote)
        banner_hover = QtDuckBannerWindow(event_advance)
        banner_hover.resize(int(banner_hover.win_w), int(banner_hover.win_h))
        banner_hover.win_x = 0
        banner_hover.tick = 30
        banner_hover.hovered_button = "plane"
        banner_hover._update_countdown_text()

        img_hover = QImage(int(banner_hover.win_w), int(banner_hover.win_h), QImage.Format.Format_ARGB32_Premultiplied)
        img_hover.fill(QColor(0, 0, 0, 0))
        p_hov = QPainter(img_hover)
        banner_hover.render(p_hov)
        p_hov.end()

        banner_hover._timer.stop()
        banner_hover.close()

        # 5. Create Combined Comparison Image (All 4 Banner States)
        total_w = max(int(banner_advance.win_w), int(banner_hover.win_w))
        banner_h = int(banner_advance.win_h)
        header_h = 75
        total_h = (banner_h + header_h) * 4 + 20

        combined = QImage(total_w, total_h, QImage.Format.Format_ARGB32_Premultiplied)
        combined.fill(QColor(30, 30, 46)) # Catppuccin Base dark background

        p_comb = QPainter(combined)
        p_comb.setRenderHint(QPainter.RenderHint.Antialiasing)

        header_font = QFont("Inter, Arial", 13, QFont.Weight.Bold)
        desc_font = QFont("Inter, Arial", 10)

        # Label 1: Advance Flyby Reminder (General Event - Slim 96px, zero buttons)
        y1 = 0
        p_comb.setFont(header_font)
        p_comb.setPen(QColor(180, 190, 254)) # Lavender
        p_comb.drawText(20, y1 + 32, "1. Advance Reminder — General Event (Stage > 0 • Adaptive Slim 96px Height)")
        p_comb.setFont(desc_font)
        p_comb.setPen(QColor(186, 194, 222))
        p_comb.drawText(20, y1 + 52, "Features: Compact 96px card (zero empty button space), [✈️ FLYBY] badge, flyby quote, Esc to dismiss")
        p_comb.drawImage(0, y1 + 65, img_advance)

        # Label 2: Advance Flyby Reminder (Online Meeting - Join Meeting only, 126px)
        y2 = y1 + banner_h + header_h
        p_comb.setFont(header_font)
        p_comb.setPen(QColor(137, 220, 235)) # Sky / Teal
        p_comb.drawText(20, y2 + 32, "2. Advance Reminder — Online Meeting (Stage > 0 • Direct Join Action, 126px)")
        p_comb.setFont(desc_font)
        p_comb.setPen(QColor(186, 194, 222))
        p_comb.drawText(20, y2 + 52, "Features: Standard 126px card, [✈️ FLYBY] badge, single [🚀 Join Flight] action button, Esc to dismiss")
        p_comb.drawImage(0, y2 + 65, img_meeting)

        # Label 3: Stage 0 Event-Time Banner (Looping Screen Alert, 126px)
        y3 = y2 + banner_h + header_h
        p_comb.setFont(header_font)
        p_comb.setPen(QColor(137, 180, 250)) # Blue
        p_comb.drawText(20, y3 + 32, "3. Event-Time Banner — Event Starting (Stage 0 • Looping Screen Alert, 126px)")
        p_comb.setFont(desc_font)
        p_comb.setPen(QColor(186, 194, 222))
        p_comb.drawText(20, y3 + 52, "Features: 'Starting Now!' badge, [✅ Got it] confirmation button required to dismiss looping screen alarm")
        p_comb.drawImage(0, y3 + 65, img_zero)

        # Label 4: Mascot Hover Reaction (Playful Quote)
        y4 = y3 + banner_h + header_h
        p_comb.setFont(header_font)
        p_comb.setPen(QColor(249, 226, 175)) # Yellow
        p_comb.drawText(20, y4 + 32, "4. Mascot Hover Interaction — Cursor Over Airplane (Playful Reaction)")
        p_comb.setFont(desc_font)
        p_comb.setPen(QColor(186, 194, 222))
        p_comb.drawText(20, y4 + 52, "Features: Dynamic mascot hover quote ('Hover mode engaged! 🛸'), pauses animation, smooth revert on mouse exit")
        p_comb.drawImage(0, y4 + 65, img_hover)

        p_comb.end()

        comparison_path = os.path.join(ARTIFACTS_DIR, "banner_visual_comparison.png")
        combined.save(comparison_path)
        self.assertTrue(os.path.exists(comparison_path))
        print(f"\n Visual comparison saved to: {comparison_path}")

    def test_render_flight_animation_dynamics(self):
        now = datetime.now().astimezone()

        # 1. Airplane Climbing (Pitch nose-up, dynamic lift float, cable tension)
        b_climb = QtDuckBannerWindow({
            "title": "Aero Climb Dynamics",
            "provider": "Google Meet",
            "start_time": now + timedelta(minutes=15),
            "pilot_type": "duck",
            "animal": "duck",
            "outfit": "aviator",
        })
        b_climb.resize(int(b_climb.win_w), int(b_climb.win_h))
        b_climb.win_x = 0
        b_climb.tick = 83 # Climb phase (negative pitch angle: nose up)
        b_climb._update_countdown_text()

        img_climb = QImage(int(b_climb.win_w), int(b_climb.win_h), QImage.Format.Format_ARGB32_Premultiplied)
        img_climb.fill(QColor(0, 0, 0, 0))
        p = QPainter(img_climb)
        b_climb.render(p)
        p.end()
        b_climb._timer.stop()
        b_climb.close()

        # 2. Level Flight with Blinking Eye & Wingtip Strobe Flash (tick=1035)
        b_blink = QtDuckBannerWindow({
            "title": "Mascot Blinking & Wingtip Beacon",
            "provider": "Google Meet",
            "start_time": now + timedelta(minutes=10),
            "pilot_type": "duck",
            "animal": "duck",
            "outfit": "aviator",
        })
        b_blink.resize(int(b_blink.win_w), int(b_blink.win_h))
        b_blink.win_x = 0
        b_blink.tick = 1035 # Simultaneous natural eye blink + wingtip strobe pulse
        b_blink._update_countdown_text()

        img_blink = QImage(int(b_blink.win_w), int(b_blink.win_h), QImage.Format.Format_ARGB32_Premultiplied)
        img_blink.fill(QColor(0, 0, 0, 0))
        p = QPainter(img_blink)
        b_blink.render(p)
        p.end()
        b_blink._timer.stop()
        b_blink.close()

        # 3. Airplane Descending (Pitch nose-down, high-speed cable flutter)
        b_dive = QtDuckBannerWindow({
            "title": "Aero Descent Dynamics",
            "provider": "Google Meet",
            "start_time": now + timedelta(minutes=5),
            "pilot_type": "duck",
            "animal": "duck",
            "outfit": "aviator",
        })
        b_dive.resize(int(b_dive.win_w), int(b_dive.win_h))
        b_dive.win_x = 0
        b_dive.tick = 0 # Descent phase (positive pitch angle: nose down)
        b_dive._update_countdown_text()

        img_dive = QImage(int(b_dive.win_w), int(b_dive.win_h), QImage.Format.Format_ARGB32_Premultiplied)
        img_dive.fill(QColor(0, 0, 0, 0))
        p = QPainter(img_dive)
        b_dive.render(p)
        p.end()
        b_dive._timer.stop()
        b_dive.close()

        # 4. Modular Mascot: Gym Bunny with Floppy Ear Inertia & Nose Twitch
        b_bunny = QtDuckBannerWindow({
            "title": "HIIT Training Session",
            "provider": "Gym Routine 🏋️",
            "start_time": now + timedelta(minutes=30),
            "pilot_type": "gym",
            "animal": "bunny",
            "outfit": "gym",
        })
        b_bunny.resize(int(b_bunny.win_w), int(b_bunny.win_h))
        b_bunny.win_x = 0
        b_bunny.tick = 42 # Active ear flutter & twitching pink nose
        b_bunny._update_countdown_text()

        img_bunny = QImage(int(b_bunny.win_w), int(b_bunny.win_h), QImage.Format.Format_ARGB32_Premultiplied)
        img_bunny.fill(QColor(0, 0, 0, 0))
        p = QPainter(img_bunny)
        b_bunny.render(p)
        p.end()
        b_bunny._timer.stop()
        b_bunny.close()

        # 5. Combine into Animation Showcase image
        total_w = int(b_climb.win_w)
        banner_h = int(b_climb.win_h)
        header_h = 75
        total_h = (banner_h + header_h) * 4 + 20

        combined = QImage(total_w, total_h, QImage.Format.Format_ARGB32_Premultiplied)
        combined.fill(QColor(30, 30, 46))

        p_comb = QPainter(combined)
        p_comb.setRenderHint(QPainter.RenderHint.Antialiasing)

        header_font = QFont("Inter, Arial", 13, QFont.Weight.Bold)
        desc_font = QFont("Inter, Arial", 10)

        # 1. Climb
        y1 = 0
        p_comb.setFont(header_font)
        p_comb.setPen(QColor(166, 227, 161)) # Green
        p_comb.drawText(20, y1 + 32, "1. Dynamic Pitch: Climbing Flight (Nose-Up ~4.2° • Aerodynamic Lift & Cable Tension)")
        p_comb.setFont(desc_font)
        p_comb.setPen(QColor(186, 194, 222))
        p_comb.drawText(20, y1 + 52, "Features: Plane pitches up naturally during vertical ascent wave, towing cables dynamically track tail hook")
        p_comb.drawImage(0, y1 + 65, img_climb)

        # 2. Blinking & Strobe
        y2 = y1 + banner_h + header_h
        p_comb.setFont(header_font)
        p_comb.setPen(QColor(180, 190, 254)) # Lavender
        p_comb.drawText(20, y2 + 32, "2. Mascot Animation: Natural Eye Blink + Navigation Wingtip Strobe Flash")
        p_comb.setFont(desc_font)
        p_comb.setPen(QColor(186, 194, 222))
        p_comb.drawText(20, y2 + 52, "Features: Pilot blinks with curved happy eyelid arc (⌒), upper wingtip emits pulsating emerald strobe bloom")
        p_comb.drawImage(0, y2 + 65, img_blink)

        # 3. Descent
        y3 = y2 + banner_h + header_h
        p_comb.setFont(header_font)
        p_comb.setPen(QColor(243, 139, 168)) # Red
        p_comb.drawText(20, y3 + 32, "3. Dynamic Pitch: Descending Flight (Nose-Down ~4.2° • Fluttering Cables & 4-Blade Propeller)")
        p_comb.setFont(desc_font)
        p_comb.setPen(QColor(186, 194, 222))
        p_comb.drawText(20, y3 + 52, "Features: Plane pitches nose-down into descent slope, dual cross-blade composite spinning prop at high RPM")
        p_comb.drawImage(0, y3 + 65, img_dive)

        # 4. Modular Mascot Bunny
        y4 = y3 + banner_h + header_h
        p_comb.setFont(header_font)
        p_comb.setPen(QColor(249, 226, 175)) # Yellow
        p_comb.drawText(20, y4 + 32, "4. Mascot Expression: Gym Bunny with Floppy Ear Slipstream Inertia & Twitching Nose")
        p_comb.setFont(desc_font)
        p_comb.setPen(QColor(186, 194, 222))
        p_comb.drawText(20, y4 + 52, "Features: Dynamic dual-wave ear tip physics, slipstream bobbing, twitching pink snout, headband & goggles")
        p_comb.drawImage(0, y4 + 65, img_bunny)

        p_comb.end()

        anim_path = os.path.join(ARTIFACTS_DIR, "flight_animation_showcase.png")
        combined.save(anim_path)
        self.assertTrue(os.path.exists(anim_path))
        print(f"\n Animation showcase saved to: {anim_path}")

if __name__ == "__main__":
    unittest.main()
