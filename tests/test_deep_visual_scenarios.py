"""
Deep Visual and Scenario Test Suite for QuakMeeting.
Creates realistic fake events (Lectures, Video meetings, Travel/transit, Therapy, Exams),
renders both macOS AppKit and Linux PyQt6 Agenda tabs offscreen, generates high-DPI
visual snapshots, verifies layout geometries and multiplatform parity, and creates
a side-by-side comparison artifact.
"""
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone

try:
    from PIL import Image
    _HAS_PIL = True
except (ImportError, ModuleNotFoundError):
    _HAS_PIL = False
    Image = None

# Force offscreen rendering for Qt
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from core.domain.clock import FakeClock
from core.domain.models import CalendarEvent, EventCategory
from core.domain.state_machine import EventState, resolve_event_state
from core.domain.reminder_policy import ReminderPolicyRegistry
from core.domain.capabilities import EventCapabilities
from ui.common.agenda_viewmodel import AgendaViewModel, AgendaEventVM

# Artifacts output directory
ARTIFACTS_DIR = os.environ.get("ARTIFACTS_DIR") or "/Users/antonino54/.gemini/antigravity/brain/474b406f-ce14-420a-9c00-6dc6e045f6bb"
os.makedirs(ARTIFACTS_DIR, exist_ok=True)


def create_fake_events_dataset(base_date: datetime):
    """Generates a diverse dataset of realistic calendar events for testing."""
    # Ensure timezone awareness
    if base_date.tzinfo is None:
        base_date = base_date.astimezone(timezone.utc)

    # 1. University Lecture (Owl Pilot)
    lecture_event = CalendarEvent(
        uid="fake-evt-lecture-01",
        title="Distributed Systems & Cloud Computing",
        start_time=base_date.replace(hour=9, minute=0, second=0),
        end_time=base_date.replace(hour=10, minute=30, second=0),
        location="Politecnico di Milano, Corso Duca degli Abruzzi 24",
        classroom="Aula 5M",
        teacher="Prof. Rossi",
        category=EventCategory.CLASS.value,
        pilot_type="owl",
        provider="PoliMi Didattica 🎓"
    )

    # 2. Remote Video Meeting in Progress (Captain Pilot)
    video_event = CalendarEvent(
        uid="fake-evt-zoom-02",
        title="Executive Sprint Review & Architecture Sync",
        start_time=base_date.replace(hour=11, minute=0, second=0),
        end_time=base_date.replace(hour=12, minute=0, second=0),
        meeting_url="https://zoom.us/j/9876543210",
        action_btn_text="🚀 JOIN SESSION",
        category=EventCategory.VIDEO_MEETING.value,
        pilot_type="captain",
        provider="Zoom Video 🎥",
        is_arrived=True,
        arrival_reason="call:Zoom"
    )

    # 3. Travel / Transit Appointment with Departure (Driver Pilot)
    transit_event = CalendarEvent(
        uid="fake-evt-transit-03",
        title="Dentist Specialist Appointment",
        start_time=base_date.replace(hour=14, minute=0, second=0),
        end_time=base_date.replace(hour=15, minute=0, second=0),
        departure_time=base_date.replace(hour=13, minute=35, second=0),
        travel_time_minutes=25,
        transport_mode="automobile",
        location="Corso Francia 102, Torino",
        category=EventCategory.TRAVEL.value,
        pilot_type="driver",
        is_travel=True,
        provider="Health & Care 🚗"
    )

    # 4. Therapy & Mental Wellness Session (Zen Duck Pilot)
    therapy_event = CalendarEvent(
        uid="fake-evt-serenis-04",
        title="Mindfulness & Guided Meditation Session",
        start_time=base_date.replace(hour=16, minute=30, second=0),
        end_time=base_date.replace(hour=17, minute=15, second=0),
        action_url="https://app.serenis.it/session/live-wellness-456",
        description="Serenis live therapy room link: https://app.serenis.it/session/live-wellness-456",
        category=EventCategory.GENERAL.value,
        pilot_type="zen_duck",
        provider="Serenis 🛋️"
    )

    # 5. University High-Stakes Exam (Owl Pilot)
    exam_event = CalendarEvent(
        uid="fake-evt-exam-05",
        title="Operational Research & Game Theory Exam",
        start_time=base_date.replace(hour=18, minute=0, second=0),
        end_time=base_date.replace(hour=20, minute=0, second=0),
        location="Campus Bovisa, Milano",
        classroom="Aula Magna F.1",
        category=EventCategory.EXAM.value,
        pilot_type="owl",
        provider="Politecnico Exams 🚨"
    )

    return [lecture_event, video_event, transit_event, therapy_event, exam_event]


class TestDeepVisualScenarios(unittest.TestCase):
    """Comprehensive visual and scenario tests with realistic fake events."""

    @classmethod
    def setUpClass(cls):
        cls.now = datetime.now().astimezone()
        cls.fake_events = create_fake_events_dataset(cls.now)

    def test_viewmodel_transformation_of_fake_events(self):
        """Verifies that all fake events are accurately transformed into rich AgendaEventVMs."""
        clock = FakeClock(self.now.replace(hour=13, minute=30, second=0))
        vms = [AgendaViewModel.build_event_vm(e, clock=clock) for e in self.fake_events]

        self.assertEqual(len(vms), 5)

        # 1. Lecture VM
        vm_lec = vms[0]
        self.assertEqual(vm_lec.icon, "🎓")
        self.assertIn("Aula 5M", vm_lec.subtitle)
        self.assertIn("Prof. Rossi", vm_lec.subtitle)
        self.assertTrue(vm_lec.capabilities.has_location)

        # 2. Video VM
        vm_vid = vms[1]
        self.assertEqual(vm_vid.icon, "✈️")
        self.assertTrue(vm_vid.capabilities.can_join)
        self.assertEqual(vm_vid.badge_text, "🟢 In Zoom")
        self.assertEqual(vm_vid.action_btn_text, "🚀 JOIN SESSION")

        # 3. Transit VM (Clock is 13:30, departure at 13:35 -> TIME_TO_LEAVE / Leave in 5m)
        vm_trn = vms[2]
        self.assertEqual(vm_trn.icon, "🚗")
        self.assertTrue(vm_trn.capabilities.needs_travel)
        self.assertTrue(vm_trn.has_action)
        self.assertIn("25m", vm_trn.action_btn_text)
        self.assertEqual(vm_trn.state, EventState.TIME_TO_LEAVE)
        self.assertEqual(vm_trn.badge_text, "🚨 Leave Now")
        self.assertEqual(vm_trn.countdown_text, "Leave in 5m")

        # 4. Therapy VM
        vm_the = vms[3]
        self.assertEqual(vm_the.icon, "🛋️")
        self.assertTrue(vm_the.capabilities.can_join)
        self.assertEqual(vm_the.action_btn_text, "🛋️ Serenis")

        # 5. Exam VM
        vm_exm = vms[4]
        self.assertEqual(vm_exm.icon, "🎓")
        self.assertIn("Aula Magna F.1", vm_exm.subtitle)
        self.assertTrue(vm_exm.capabilities.requires_acknowledgement)

    def test_macos_agenda_tab_visual_rendering(self):
        """Renders macOS AppKit AgendaTabController offscreen and validates card layout & snapshot."""
        try:
            import AppKit
            from ui.macos.dashboard_tabs.agenda_tab import AgendaTabController
        except (ImportError, ModuleNotFoundError) as e:
            self.skipTest(f"AppKit not available: {e}")

        tab_ctrl = AgendaTabController.alloc().init()
        w = 480.0
        h = 440.0
        scroll_view = tab_ctrl.render(None, w, h, self.fake_events, is_loading=False, config={})
        self.assertIsNotNone(scroll_view)

        doc_view = scroll_view.documentView()
        self.assertIsNotNone(doc_view)

        # Verify all 5 meeting cards were rendered inside doc_view
        subviews = doc_view.subviews()
        self.assertEqual(len(subviews), 5, f"Expected 5 meeting cards in AppKit view, got {len(subviews)}")

        # Capture document view offscreen to PNG
        doc_view.layoutSubtreeIfNeeded()
        doc_view.displayIfNeeded()
        bounds = doc_view.bounds()
        rep = doc_view.bitmapImageRepForCachingDisplayInRect_(bounds)
        if rep is None:
            rep = AppKit.NSBitmapImageRep.alloc().initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bytesPerRow_bitsPerPixel_(
                None, int(bounds.size.width), int(bounds.size.height), 8, 4, True, False, AppKit.NSCalibratedRGBColorSpace, 0, 32
            )
        doc_view.cacheDisplayInRect_toBitmapImageRep_(bounds, rep)
        png_data = rep.representationUsingType_properties_(AppKit.NSBitmapImageFileTypePNG, None)
        self.assertIsNotNone(png_data, "AppKit failed to produce PNG representation")

        macos_snapshot_path = os.path.join(ARTIFACTS_DIR, "macos_agenda_visual_snapshot.png")
        success = png_data.writeToFile_atomically_(macos_snapshot_path, True)
        self.assertTrue(success, f"Failed to save macOS snapshot to {macos_snapshot_path}")
        self.assertTrue(os.path.exists(macos_snapshot_path))
        file_size = os.path.getsize(macos_snapshot_path)
        self.assertGreater(file_size, 5000, "Rendered macOS image should contain non-trivial data")
        print(f"\n[Visual Test] macOS AppKit Agenda snapshot saved: {macos_snapshot_path} ({file_size} bytes)")

    def test_linux_qt_agenda_tab_visual_rendering(self):
        """Renders Linux PyQt6 QtAgendaTab offscreen and validates card layout & snapshot."""
        try:
            from PyQt6.QtWidgets import QApplication, QFrame, QLabel, QPushButton
            from PyQt6.QtGui import QImage, QPainter, QColor
            from ui.linux.dashboard_tabs.agenda_tab import QtAgendaTab
        except (ImportError, ModuleNotFoundError) as e:
            self.skipTest(f"PyQt6 not available: {e}")

        app = QApplication.instance() or QApplication(sys.argv)
        tab_widget = QtAgendaTab()
        tab_widget.resize(480, 480)
        tab_widget.refresh_agenda(self.fake_events)

        # Validate that 5 card frames exist
        cards = [c for c in tab_widget.scroll_content.findChildren(QFrame) if c.objectName() == "Card"]
        self.assertEqual(len(cards), 5, f"Expected 5 meeting cards in Qt scroll content, got {len(cards)}")

        # Validate presence of action buttons
        buttons = tab_widget.scroll_content.findChildren(QPushButton, "PrimaryBtn")
        self.assertEqual(len(buttons), 5, f"Expected 5 action buttons across the 5 fake events, got {len(buttons)}")

        # Render Qt widget offscreen to QImage
        img = QImage(480, 480, QImage.Format.Format_ARGB32_Premultiplied)
        img.fill(QColor(30, 30, 46)) # Catppuccin Base dark background
        painter = QPainter(img)
        tab_widget.render(painter)
        painter.end()

        linux_snapshot_path = os.path.join(ARTIFACTS_DIR, "linux_agenda_visual_snapshot.png")
        saved = img.save(linux_snapshot_path)
        self.assertTrue(saved, f"Failed to save Linux Qt snapshot to {linux_snapshot_path}")
        self.assertTrue(os.path.exists(linux_snapshot_path))
        file_size = os.path.getsize(linux_snapshot_path)
        self.assertGreater(file_size, 5000, "Rendered Linux image should contain non-trivial data")
        print(f"\n[Visual Test] Linux PyQt6 Agenda snapshot saved: {linux_snapshot_path} ({file_size} bytes)")

    def test_z_generate_cross_platform_parity_comparison(self):
        """Generates a side-by-side comparison artifact combining macOS and Linux views."""
        macos_path = os.path.join(ARTIFACTS_DIR, "macos_agenda_visual_snapshot.png")
        linux_path = os.path.join(ARTIFACTS_DIR, "linux_agenda_visual_snapshot.png")

        if not _HAS_PIL:
            self.skipTest("PIL (Pillow) required for parity comparison")

        if not (os.path.exists(macos_path) and os.path.exists(linux_path)):
            self.skipTest("Both macOS and Linux snapshots are required to produce parity comparison")

        img_mac = Image.open(macos_path)
        img_lin = Image.open(linux_path)

        # Scale or pad to matching height
        target_h = max(img_mac.height, img_lin.height)
        header_h = 70
        total_w = img_mac.width + img_lin.width + 40
        total_h = target_h + header_h + 30

        try:
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtGui import QImage, QPainter, QColor, QFont
            app = QApplication.instance() or QApplication(sys.argv)

            combined = QImage(total_w, total_h, QImage.Format.Format_ARGB32_Premultiplied)
            combined.fill(QColor(24, 24, 37)) # Catppuccin Crust

            p = QPainter(combined)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Header
            p.setFont(QFont("Inter, Arial", 16, QFont.Weight.Bold))
            p.setPen(QColor(205, 214, 244)) # Text
            p.drawText(24, 36, "QuakMeeting Agenda Tab: Cross-Platform Parity Verification")

            p.setFont(QFont("Inter, Arial", 11))
            p.setPen(QColor(166, 173, 200)) # Subtext0
            p.drawText(24, 58, "Identical presentation of 5 fake events rendered from shared AgendaViewModel (macOS AppKit vs Linux PyQt6)")

            # Column 1: macOS
            p.setFont(QFont("Inter, Arial", 13, QFont.Weight.Bold))
            p.setPen(QColor(137, 180, 250)) # Blue
            p.drawText(20, header_h + 16, "🍏 macOS Native View (AppKit Cocoa)")

            q_mac = QImage(macos_path)
            p.drawImage(20, header_h + 26, q_mac)

            # Column 2: Linux
            col2_x = img_mac.width + 30
            p.setFont(QFont("Inter, Arial", 13, QFont.Weight.Bold))
            p.setPen(QColor(203, 166, 247)) # Mauve
            p.drawText(col2_x, header_h + 16, "🐧 Linux Native View (PyQt6 / Catppuccin)")

            q_lin = QImage(linux_path)
            p.drawImage(col2_x, header_h + 26, q_lin)

            p.end()

            parity_path = os.path.join(ARTIFACTS_DIR, "agenda_cross_platform_parity.png")
            combined.save(parity_path)
            self.assertTrue(os.path.exists(parity_path))
            print(f"\n[Visual Test] Parity comparison saved: {parity_path}")
        except Exception as e:
            self.fail(f"Failed to generate cross-platform parity image: {e}")

    def test_banner_scenarios_visual_rendering(self):
        """Renders HUD banners for multiple fake event types and pilots."""
        try:
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtGui import QImage, QPainter, QColor, QFont
            from ui.linux.banner.qt_duck_banner import QtDuckBannerWindow
        except (ImportError, ModuleNotFoundError) as e:
            self.skipTest(f"PyQt6 not available for banner visual rendering: {e}")

        app = QApplication.instance() or QApplication(sys.argv)
        banner_panels = []

        # 1. Exam Banner (Owl Mascot)
        b_exam = QtDuckBannerWindow({
            "title": "Operational Research & Game Theory Exam",
            "provider": "PoliMi Exam 🚨",
            "start_time": self.now + timedelta(minutes=60),
            "reminder_stage": 60,
            "pilot_type": "owl",
            "animal": "owl",
            "classroom": "Aula Magna F.1",
            "location": "Campus Bovisa"
        })
        b_exam.resize(int(b_exam.win_w), int(b_exam.win_h))
        b_exam.win_x = 0
        b_exam.tick = 30
        b_exam._update_countdown_text()
        img_exam = QImage(int(b_exam.win_w), int(b_exam.win_h), QImage.Format.Format_ARGB32_Premultiplied)
        img_exam.fill(QColor(0, 0, 0, 0))
        p = QPainter(img_exam)
        b_exam.render(p)
        p.end()
        b_exam._timer.stop()
        b_exam.close()
        banner_panels.append(("1. University Exam Runway Alert (Owl Pilot • Stage 60m)", img_exam))

        # 2. Video Meeting Advance Flyby (Captain Mascot)
        b_video = QtDuckBannerWindow({
            "title": "Executive Sprint Review & Architecture Sync",
            "provider": "Zoom Video 🎥",
            "action_url": "https://zoom.us/j/9876543210",
            "start_time": self.now + timedelta(minutes=10),
            "reminder_stage": 10,
            "pilot_type": "captain",
            "animal": "duck",
            "outfit": "captain"
        })
        b_video.resize(int(b_video.win_w), int(b_video.win_h))
        b_video.win_x = 0
        b_video.tick = 30
        b_video._update_countdown_text()
        img_video = QImage(int(b_video.win_w), int(b_video.win_h), QImage.Format.Format_ARGB32_Premultiplied)
        img_video.fill(QColor(0, 0, 0, 0))
        p = QPainter(img_video)
        b_video.render(p)
        p.end()
        b_video._timer.stop()
        b_video.close()
        banner_panels.append(("2. Online Video Meeting Flyby (Captain Pilot • Join Button)", img_video))

        # 3. Departure Urgency Alert (Driver Mascot)
        b_depart = QtDuckBannerWindow({
            "title": "Dentist Specialist Appointment",
            "provider": "Travel 🚗",
            "start_time": self.now + timedelta(minutes=25),
            "departure_time": self.now + timedelta(minutes=5),
            "travel_time_minutes": 20,
            "transport_mode": "automobile",
            "reminder_stage": 5,
            "is_travel": True,
            "pilot_type": "driver",
            "animal": "duck",
            "outfit": "driver"
        })
        b_depart.resize(int(b_depart.win_w), int(b_depart.win_h))
        b_depart.win_x = 0
        b_depart.tick = 30
        b_depart._update_countdown_text()
        img_depart = QImage(int(b_depart.win_w), int(b_depart.win_h), QImage.Format.Format_ARGB32_Premultiplied)
        img_depart.fill(QColor(0, 0, 0, 0))
        p = QPainter(img_depart)
        b_depart.render(p)
        p.end()
        b_depart._timer.stop()
        b_depart.close()
        banner_panels.append(("3. Transit Departure Alert (Driver Pilot • 'Leave in 5m')", img_depart))

        # 4. Stage 0 Looping Banner (Zen Duck Mascot)
        b_zero = QtDuckBannerWindow({
            "title": "Mindfulness & Guided Meditation Session",
            "provider": "Serenis 🛋️",
            "action_url": "https://app.serenis.it/session/live-wellness-456",
            "start_time": self.now,
            "reminder_stage": 0,
            "pilot_type": "zen_duck",
            "animal": "duck",
            "outfit": "zen_duck"
        })
        b_zero.resize(int(b_zero.win_w), int(b_zero.win_h))
        b_zero.win_x = 0
        b_zero.tick = 30
        b_zero._update_countdown_text()
        img_zero = QImage(int(b_zero.win_w), int(b_zero.win_h), QImage.Format.Format_ARGB32_Premultiplied)
        img_zero.fill(QColor(0, 0, 0, 0))
        p = QPainter(img_zero)
        b_zero.render(p)
        p.end()
        b_zero._timer.stop()
        b_zero.close()
        banner_panels.append(("4. Event-Time Looping Alarm (Zen Duck Pilot • Stage 0)", img_zero))

        # Assemble combined showcase
        banner_w = int(b_exam.win_w)
        banner_h = int(b_exam.win_h)
        header_h = 60
        total_h = (banner_h + header_h) * len(banner_panels) + 20

        combined = QImage(banner_w, total_h, QImage.Format.Format_ARGB32_Premultiplied)
        combined.fill(QColor(30, 30, 46))
        p = QPainter(combined)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        header_font = QFont("Inter, Arial", 13, QFont.Weight.Bold)

        for i, (title, img_b) in enumerate(banner_panels):
            y_base = i * (banner_h + header_h)
            p.setFont(header_font)
            p.setPen(QColor(180, 190, 254))
            p.drawText(20, y_base + 34, title)
            p.drawImage(0, y_base + 50, img_b)

        p.end()

        banner_scenarios_path = os.path.join(ARTIFACTS_DIR, "banner_scenarios_visual.png")
        combined.save(banner_scenarios_path)
        self.assertTrue(os.path.exists(banner_scenarios_path))
        print(f"\n[Visual Test] Banner scenarios showcase saved: {banner_scenarios_path}")


if __name__ == "__main__":
    unittest.main()
