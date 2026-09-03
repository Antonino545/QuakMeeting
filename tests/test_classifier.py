import unittest
from datetime import datetime
from core.domain.classifier import EventClassifier
from core.domain.models import PilotType, EventCategory

class TestEventClassifier(unittest.TestCase):
    def setUp(self):
        self.classifier = EventClassifier()
        from unittest.mock import patch
        self._patcher = patch("core.services.config_service.config.get", side_effect=lambda k, d=None: {
            "default_pilot": "duck",
            "force_default_pilot": False,
            "mascot_customization": {
                "study": {"animal": "owl", "outfit": "student"},
                "class": {"animal": "owl", "outfit": "student"},
                "food": {"animal": "duck", "outfit": "chef"},
                "travel": {"animal": "duck", "outfit": "captain"},
                "sport": {"animal": "duck", "outfit": "gym"},
                "in_person": {"animal": "duck", "outfit": "racer"},
                "health": {"animal": "duck", "outfit": "zen"},
                "general": {"animal": "duck", "outfit": "aviator"}
            }
        }.get(k, d))
        self._patcher.start()

    def tearDown(self):
        self._patcher.stop()

    def test_extract_meeting_url(self):
        meet_text = "Join us at https://meet.google.com/abc-defg-hij please!"
        self.assertEqual(EventClassifier.extract_meeting_url(meet_text), "https://meet.google.com/abc-defg-hij")

        zoom_text = "Click here: https://company.zoom.us/j/123456789?pwd=xyz"
        self.assertEqual(EventClassifier.extract_meeting_url(zoom_text), "https://company.zoom.us/j/123456789?pwd=xyz")

        serenis_text = "Link: https://app.serenis.it/join/abc_123"
        self.assertEqual(EventClassifier.extract_meeting_url(serenis_text), "https://app.serenis.it/join/abc_123")

        self.assertIsNone(EventClassifier.extract_meeting_url(None))
        self.assertIsNone(EventClassifier.extract_meeting_url("missing value"))
        self.assertIsNone(EventClassifier.extract_meeting_url("No link here at all"))

    def test_classify_flight_travel(self):
        meeting = self.classifier.classify(
            title="Flight to London (BA 257)",
            location="Terminal 5 - Gate B12",
            description=""
        )
        self.assertEqual(meeting.pilot_type, PilotType.CAPTAIN.value)
        self.assertEqual(meeting.event_type, EventCategory.TRAVEL.value)
        self.assertTrue(meeting.is_travel)
        self.assertIn("maps.apple.com", meeting.action_url)

    def test_classify_food_dinner(self):
        meeting = self.classifier.classify(
            title="Dinner with team",
            location="Mario Pizzeria",
            description=""
        )
        self.assertEqual(meeting.pilot_type, PilotType.CHEF.value)
        self.assertEqual(meeting.event_type, EventCategory.FOOD.value)
        self.assertTrue(meeting.is_travel)

    def test_classify_video_meetings(self):
        meeting = self.classifier.classify(
            title="Sprint Planning",
            location="",
            description="https://meet.google.com/xyz-uvw-rst"
        )
        self.assertEqual(meeting.pilot_type, PilotType.DUCK.value)
        self.assertEqual(meeting.event_type, EventCategory.VIDEO_MEETING.value)
        self.assertFalse(meeting.is_travel)
        self.assertEqual(meeting.action_url, "https://meet.google.com/xyz-uvw-rst")

    def test_classify_class_and_study(self):
        # 1. Lecture / Classroom Attendance -> EventCategory.CLASS
        m_lecture = self.classifier.classify(
            title="Neural Networks University Lecture",
            location="Room 3B",
            description=""
        )
        self.assertEqual(m_lecture.pilot_type, PilotType.OWL.value)
        self.assertEqual(m_lecture.event_type, EventCategory.CLASS.value)
        self.assertIn("Class / Lecture", m_lecture.provider)

        # 2. Self-Study Block -> EventCategory.STUDY
        m_study = self.classifier.classify(
            title="Self-Study: Review Neural Networks notes",
            location="",
            description=""
        )
        self.assertEqual(m_study.pilot_type, PilotType.OWL.value)
        self.assertEqual(m_study.event_type, EventCategory.STUDY.value)
        self.assertEqual(m_study.provider, "Study Session 📖")

        # 3. OR Study & LP/MILP Modeling Template -> EventCategory.STUDY
        m_or_study = self.classifier.classify(
            title="OR Study: Intro & LP/MILP Modeling Template",
            location="",
            description=""
        )
        self.assertEqual(m_or_study.pilot_type, PilotType.OWL.value)
        self.assertEqual(m_or_study.event_type, EventCategory.STUDY.value)
        self.assertEqual(m_or_study.provider, "Study Session 📖")

        # 4. Self study with space and location -> EventCategory.STUDY
        m_self_study = self.classifier.classify(
            title="Self study for ICT course",
            location="Aula 5M",
            description=""
        )
        self.assertEqual(m_self_study.pilot_type, PilotType.OWL.value)
        self.assertEqual(m_self_study.event_type, EventCategory.STUDY.value)
        self.assertEqual(m_self_study.provider, "Study Session 📖")

        m_study_with_exam_reference = self.classifier.classify(
            title="OR Study: Finish Lecture 3 (Complexity P, NP, NP-Complete)",
            description="Goal: master standard exam examples and certificate verification.",
        )
        self.assertEqual(m_study_with_exam_reference.event_type, EventCategory.STUDY.value)
        self.assertEqual(m_study_with_exam_reference.provider, "Study Session 📖")

    def test_classroom_and_teacher_extraction(self):
        title = "ICT for smart mobility (VASSIO LUCA) - Aula 5M"
        meeting = self.classifier.classify(title=title, location="Politecnico")
        self.assertEqual(meeting.pilot_type, PilotType.OWL.value)
        self.assertEqual(meeting.event_type, EventCategory.CLASS.value)
        self.assertEqual(meeting.classroom, "Aula 5M")
        self.assertEqual(meeting.teacher, "VASSIO LUCA")
        self.assertIn("Aula 5M", meeting.provider)

    def test_classify_zen_duck(self):
        meeting = self.classifier.classify(
            title="Serenis Online Therapy Session",
            location="",
            description="https://app.serenis.it/join/test123"
        )
        self.assertEqual(meeting.pilot_type, PilotType.ZEN_DUCK.value)
        self.assertEqual(meeting.provider, "Serenis 🛋️")

    def test_classify_gym_sport(self):
        # 1. Palestra / Workout
        m1 = self.classifier.classify(title="Allenamento in Palestra con Pesi", location="Gold Gym")
        self.assertEqual(m1.pilot_type, PilotType.GYM.value)
        self.assertEqual(m1.event_type, EventCategory.SPORT.value)
        self.assertTrue(m1.is_travel)
        self.assertIn("Gym & Sport", m1.provider)

        # 2. Padel / Calcio Match
        m2 = self.classifier.classify(title="Partita di Padel con amici", location="Padel Club Torino")
        self.assertEqual(m2.pilot_type, PilotType.GYM.value)
        self.assertEqual(m2.event_type, EventCategory.SPORT.value)
        self.assertTrue(m2.is_travel)

    def test_classify_platypus_and_squirrel(self):
        # 1. Platypus secret mission
        m_plat = self.classifier.classify(title="Top Secret Agent Mission Briefing", location="")
        self.assertEqual(m_plat.pilot_type, PilotType.PLATYPUS.value)
        self.assertIn("Secret Mission", m_plat.provider)

        # 2. Squirrel quick sync / brainstorm
        m_squir = self.classifier.classify(title="Hackathon Sprint Planning & Quick Sync", location="")
        self.assertEqual(m_squir.pilot_type, PilotType.SQUIRREL.value)
        self.assertIn("Quick Sync", m_squir.provider)

    def test_default_pilot_customization(self):
        from unittest.mock import patch
        from core.services.config_service import DEFAULT_CONFIG

        def mock_get_def(k, d=None):
            if k == "default_pilot":
                return "platypus"
            return DEFAULT_CONFIG.get(k, d)

        with patch("core.services.config_service.config.get", side_effect=mock_get_def):
            meeting = self.classifier.classify(title="General unclassified discussion", location="")
            self.assertEqual(meeting.animal, "platypus")

        def mock_get_forced(k, d=None):
            if k == "force_default_pilot":
                return True
            if k == "default_pilot":
                return "bunny"
            return DEFAULT_CONFIG.get(k, d)

        with patch("core.services.config_service.config.get", side_effect=mock_get_forced):
            meeting = self.classifier.classify(title="Dinner with team", location="Pizzeria")
            self.assertEqual(meeting.animal, "bunny")
            self.assertEqual(meeting.pilot_type, "bunny_chef")

    def test_modular_mascot_customization(self):
        from unittest.mock import patch
        from core.services.config_service import DEFAULT_CONFIG

        customs = {
            "study": {"animal": "bunny", "outfit": "student"},
            "food": {"animal": "owl", "outfit": "chef"}
        }

        def mock_get_customs(k, d=None):
            if k == "mascot_customization":
                return customs
            return DEFAULT_CONFIG.get(k, d)

        with patch("core.services.config_service.config.get", side_effect=mock_get_customs):
            # Study event -> Bunny with Student Hat
            m_study = self.classifier.classify(title="Studiare Fisica e Matematica", location="")
            self.assertEqual(m_study.animal, "bunny")
            self.assertEqual(m_study.outfit, "student")
            self.assertEqual(m_study.pilot_type, "bunny_student")

            # Food event -> Owl with Chef Hat
            m_food = self.classifier.classify(title="Cena con amici", location="Pizzeria")
            self.assertEqual(m_food.animal, "owl")
            self.assertEqual(m_food.outfit, "chef")
            self.assertEqual(m_food.pilot_type, "owl_chef")

    def test_classify_exam_events(self):
        # 1. Exam with prefix "Exam:..."
        m1 = self.classifier.classify(
            title="Exam:Satellite Systems for Positioning and Maps",
            location="Politecnico di Torino",
            description=""
        )
        self.assertEqual(m1.event_type, EventCategory.EXAM.value)
        self.assertEqual(m1.pilot_type, PilotType.OWL.value)
        self.assertTrue(m1.is_travel)
        self.assertIn("Exam", m1.provider)

        # 2. Italian Esame with "Esame di..."
        m2 = self.classifier.classify(
            title="Esame di Analisi Matematica 1 - Aula 5M",
            location="Politecnico",
            description=""
        )
        self.assertEqual(m2.event_type, EventCategory.EXAM.value)
        self.assertEqual(m2.classroom, "Aula 5M")
        self.assertTrue(m2.is_travel)

        # 3. Midterm / Appello / Parziale
        m3 = self.classifier.classify(
            title="Appello Sessione Invernale: Fisica Generale",
            location="Aula Magna",
            description=""
        )
        self.assertEqual(m3.event_type, EventCategory.EXAM.value)
        self.assertTrue(m3.is_travel)

    def test_temporal_anchors_and_hard_cases_regression(self):
        """Unified regression test covering all original and hard temporal anchor cases (Section 3.1, 3.2, 3.3)."""
        cases = [
            # 3.1 Original cases
            ("OR Study: Lecture 4 - Simplex & Duality (After Dinner Session)", "", "", EventCategory.STUDY, PilotType.OWL),
            ("Study session (after dinner)", "", "", EventCategory.STUDY, None),
            ("Gym workout before dinner", "", "", EventCategory.SPORT, None),
            ("Quick sync after lunch", "", "", EventCategory.GENERAL, PilotType.SQUIRREL),
            ("Dentist appointment after breakfast", "", "", EventCategory.IN_PERSON, PilotType.DRIVER),
            ("OR Study: Lecture 2 (Post-Workout Session)", "", "", EventCategory.STUDY, None),
            ("Dinner after gym", "", "", EventCategory.FOOD, None),
            ("Cena dopo la palestra", "", "", EventCategory.FOOD, None),
            ("Quick sync after workout", "", "", EventCategory.GENERAL, PilotType.SQUIRREL),
            ("Dinner after exam", "", "", EventCategory.FOOD, None),
            ("Pizza post-esame", "", "", EventCategory.FOOD, None),
            ("Drinks after class", "", "", EventCategory.FOOD, None),
            ("Relax after exam", "", "", EventCategory.HEALTH, PilotType.ZEN_DUCK),
            ("Gym after class", "", "", EventCategory.SPORT, None),
            ("Quick sync before flight", "", "", EventCategory.GENERAL, PilotType.SQUIRREL),
            ("Dinner after flight", "", "", EventCategory.FOOD, None),
            ("Study on train", "", "", EventCategory.STUDY, None),
            ("Gym after work", "", "", EventCategory.SPORT, None),
            ("Palestra dopo lavoro", "", "", EventCategory.SPORT, None),
            ("Dinner after work", "", "", EventCategory.FOOD, None),
            ("Cena dopo l'ufficio", "", "", EventCategory.FOOD, None),
            ("Dinner with team", "Mario Pizzeria", "", EventCategory.FOOD, None),
            ("Mario Pizzeria", "", "", EventCategory.FOOD, None),
            ("Dinner with study group", "", "", EventCategory.FOOD, None),
            ("Lunch with Professor Rossi", "", "", EventCategory.FOOD, None),
            ("Aperitivo pre-cena", "", "", EventCategory.FOOD, None),
            ("Flight to London (BA 257)", "Terminal 5", "dinner served", EventCategory.TRAVEL, None),

            # 3.2 New hard cases
            ("Dinner after gym after work", "", "", EventCategory.FOOD, None),
            ("Quick sync after gym, before dinner", "", "", EventCategory.GENERAL, PilotType.SQUIRREL),
            ("After gym", "", "", EventCategory.SPORT, None),
            ("Café Luna team lunch", "", "", EventCategory.FOOD, None),
            ("Training Room booking", "", "", EventCategory.GENERAL, None),
            ("Exam Room 3 - IT setup check", "", "", EventCategory.GENERAL, None),
            ("Study: Dinner reservation for 4", "", "", EventCategory.FOOD, None),
            ("Weekly Sync (was: Lunch review)", "", "", EventCategory.GENERAL, None),
            ("Cancelled: dinner after gym", "", "", EventCategory.FOOD, None),
            ("[TENTATIVE] Gym before flight", "", "", EventCategory.SPORT, None),
            ("Coffee after dentist", "", "", EventCategory.FOOD, None),
            ("Study group after exam", "", "", EventCategory.STUDY, None),
            ("Nap before exam", "", "", EventCategory.HEALTH, None),
            ("Riposo prima dell'esame", "", "", EventCategory.HEALTH, None),
            ("Meeting at 5, before flight", "", "", EventCategory.GENERAL, None),
            ("Meeting before 5pm flight", "", "", EventCategory.GENERAL, None),
            ("Lunch and Learn: Q3 Roadmap", "", "", EventCategory.GENERAL, None),
            ("Coffee chat with recruiter", "", "", EventCategory.IN_PERSON, None),
        ]

        for item in cases:
            title, location, desc, expected_cat, expected_pilot = item
            with self.subTest(title=title):
                meeting = self.classifier.classify(title=title, location=location, description=desc)
                self.assertEqual(
                    meeting.event_type, expected_cat.value,
                    f"Expected event_type {expected_cat.value} for title '{title}', got {meeting.event_type}"
                )
                if expected_pilot is not None:
                    self.assertEqual(
                        meeting.pilot_type, expected_pilot.value,
                        f"Expected pilot_type {expected_pilot.value} for title '{title}', got {meeting.pilot_type}"
                    )



