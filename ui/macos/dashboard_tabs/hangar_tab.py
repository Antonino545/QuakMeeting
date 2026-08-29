import AppKit
import objc
from datetime import datetime

try:
    from ui.macos.banner_window import _run_banner
    from ui.macos.theme import Theme
except ImportError:
    from banner_window import _run_banner
    from theme import Theme

class HangarTabController(AppKit.NSObject):
    def init(self):
        self = objc.super(HangarTabController, self).init()
        self.dashboard_controller = None
        return self

    @objc.python_method
    def render(self, container, w, h):
        self.dashboard_controller = container

        scroll_view = AppKit.NSScrollView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w, h))
        scroll_view.setHasVerticalScroller_(True)
        scroll_view.setDrawsBackground_(False)

        pilots = [
            ("duck", "🦆 Aviator Duck", "Video conferences: Google Meet, Zoom, MS Teams & online meetings.", "Catppuccin Green", self.testAviatorDuck_),
            ("chef", "👨‍🍳 Chef Duck & Food", "Dinners, Lunches, Restaurants, Pizzerias & Apple Maps food routes.", "Catppuccin Peach", self.testChefDuck_),
            ("captain", "🧑‍✈️ Jet Airliner Captain", "Airline Flights, Airports, High-speed trains, Buses & Travel Routes.", "Catppuccin Sapphire", self.testCaptainJet_),
            ("owl", "🦉 Academic Owl", "University Lectures, Exams, Campus courses & Study sessions.", "Catppuccin Mauve", self.testAcademicOwl_),
            ("gym", "🏋️‍♂️ Athlete Duck & Palestra", "Palestra, Gym workouts, CrossFit, Padel, Tennis, Calcio & Sport training.", "Catppuccin Red", self.testGymDuck_),
            ("driver", "🏎️ Speed Racer Driver", "In-person appointments, Doctor visits, Office & Real-Time Navigation.", "Catppuccin Yellow", self.testSpeedRacer_),
            ("zen_duck", "🦆🌸 Zen Duck", "Serenis sessions, Psychological Therapy, Yoga, Wellness & Meditation.", "Catppuccin Teal", self.testZenDuck_)
        ]

        card_h = 108.0
        gap = 14.0
        content_h = len(pilots) * (card_h + gap) + 20.0

        doc_view = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w, content_h))

        for idx, (p_id, p_name, p_desc, p_theme, p_action) in enumerate(pilots):
            y_item = content_h - (idx + 1) * (card_h + gap)
            card = self._create_pilot_card(p_id, p_name, p_desc, p_theme, p_action, 0, y_item, w - 16, card_h)
            doc_view.addSubview_(card)

        scroll_view.setDocumentView_(doc_view)
        if scroll_view.contentView():
            scroll_view.contentView().scrollToPoint_(AppKit.NSMakePoint(0, content_h - h))
        return scroll_view

    @objc.python_method
    def _create_pilot_card(self, p_id, p_name, p_desc, p_theme, p_action, x, y, w, h):
        card = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(x, y, w, h))
        card.setWantsLayer_(True)
        card.layer().setBackgroundColor_(Theme.BASE.CGColor())
        card.layer().setCornerRadius_(12.0)
        card.layer().setMasksToBounds_(True)
        card.layer().setBorderWidth_(1.0)
        card.layer().setBorderColor_(Theme.SURFACE0.CGColor())

        title_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(20, h - 38, w - 210, 26))
        title_lbl.setStringValue_(p_name)
        title_lbl.setFont_(AppKit.NSFont.boldSystemFontOfSize_(15))
        title_lbl.setTextColor_(Theme.TEXT)
        title_lbl.setBezeled_(False)
        title_lbl.setDrawsBackground_(False)
        title_lbl.setEditable_(False)
        card.addSubview_(title_lbl)

        desc_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(20, h - 70, w - 210, 32))
        desc_lbl.setStringValue_(p_desc)
        desc_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(12))
        desc_lbl.setTextColor_(Theme.SUBTEXT0)
        desc_lbl.setBezeled_(False)
        desc_lbl.setDrawsBackground_(False)
        desc_lbl.setEditable_(False)
        card.addSubview_(desc_lbl)

        tag_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(20, 12, 180, 20))
        tag_lbl.setStringValue_(f"🎨 Theme: {p_theme}")
        tag_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(11))
        tag_lbl.setTextColor_(Theme.SUBTEXT1)
        tag_lbl.setBezeled_(False)
        tag_lbl.setDrawsBackground_(False)
        tag_lbl.setEditable_(False)
        card.addSubview_(tag_lbl)

        test_btn = AppKit.NSButton.alloc().initWithFrame_(AppKit.NSMakeRect(w - 180, (h - 38) * 0.5, 160, 38))
        test_btn.setTitle_("🚀 Test Flight")
        test_btn.setBezelStyle_(AppKit.NSBezelStyleRounded)
        test_btn.setFont_(AppKit.NSFont.boldSystemFontOfSize_(13))
        test_btn.setTarget_(self)
        test_btn.setAction_(p_action.__name__.rstrip('_') + ":")
        card.addSubview_(test_btn)

        return card

    @objc.IBAction
    def testAviatorDuck_(self, sender):
        _run_banner({
            "title": "Weekly Sprint Planning (Google Meet)",
            "provider": "Google Meet 🟢",
            "pilot_type": "duck",
            "action_btn_text": "🚀 JOIN GOOGLE MEET",
            "action_url": "https://meet.google.com/test-quak",
            "start_time": datetime.now().astimezone(),
            "is_travel": False
        })

    @objc.IBAction
    def testChefDuck_(self, sender):
        _run_banner({
            "title": "Dinner with Friends at Pizzeria",
            "provider": "Dinner / Food 🍕🍽️",
            "pilot_type": "chef",
            "action_btn_text": "🗺️ RESTAURANT DIRECTIONS (MAPS)",
            "action_url": "https://maps.apple.com/?q=Pizzeria+Napoli",
            "location": "Pizzeria Da Michele, London",
            "start_time": datetime.now().astimezone(),
            "is_travel": True
        })

    @objc.IBAction
    def testCaptainJet_(self, sender):
        _run_banner({
            "title": "Flight to London (BA 257)",
            "provider": "Flight / Travel ✈️",
            "pilot_type": "captain",
            "action_btn_text": "🗺️ AIRPORT DIRECTIONS (MAPS)",
            "action_url": "https://maps.apple.com/?q=Heathrow+Airport",
            "location": "Terminal 5 - Gate B12",
            "start_time": datetime.now().astimezone(),
            "is_travel": True
        })

    @objc.IBAction
    def testAcademicOwl_(self, sender):
        _run_banner({
            "title": "ICT for smart mobility (VASSIO LUCA) - Aula 5M",
            "provider": "Study / Class 🎓 Aula 5M",
            "pilot_type": "owl",
            "classroom": "Aula 5M",
            "teacher": "VASSIO LUCA",
            "action_btn_text": "📚 CLASSROOM & NOTES",
            "action_url": "https://calendar.apple.com",
            "location": "Politecnico - Aula 5M",
            "start_time": datetime.now().astimezone(),
            "is_travel": False
        })

    @objc.IBAction
    def testGymDuck_(self, sender):
        _run_banner({
            "title": "CrossFit & Palestra Workout Session",
            "provider": "Gym & Sport 🏋️‍♂️💪",
            "pilot_type": "gym",
            "action_btn_text": "🗺️ GYM DIRECTIONS (MAPS)",
            "action_url": "https://maps.apple.com/?daddr=CrossFit+Gym",
            "location": "Downtown Gym & Fitness Club",
            "start_time": datetime.now().astimezone(),
            "is_travel": True
        })

    @objc.IBAction
    def testSpeedRacer_(self, sender):
        _run_banner({
            "title": "Studio Architecture Meeting",
            "provider": "In Person 📍 Travel Time!",
            "pilot_type": "driver",
            "action_btn_text": "🗺️ NAVIGATE WITH MAPS",
            "action_url": "https://maps.apple.com/?daddr=Studio+Design",
            "location": "Via Roma 10, Downtown",
            "start_time": datetime.now().astimezone(),
            "is_travel": True
        })

    @objc.IBAction
    def testZenDuck_(self, sender):
        _run_banner({
            "title": "Serenis Online Therapy Session",
            "provider": "Serenis 🛋️",
            "pilot_type": "zen_duck",
            "action_btn_text": "🚀 JOIN SESSION",
            "action_url": "https://app.serenis.it/join/test",
            "start_time": datetime.now().astimezone(),
            "is_travel": False
        })
