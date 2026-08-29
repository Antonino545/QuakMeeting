"""
Unit Tests for Language and Internationalization Service:
- Detection of system locale
- Language resolution ('system', 'en', 'it')
- Translation lookup and parameter interpolation
- Fallback mechanics
"""
import unittest
from core.services.language_service import (
    detect_system_language,
    get_active_language,
    t,
    TRANSLATIONS
)

class TestLanguageService(unittest.TestCase):

    def test_translations_coverage(self):
        # Verify both English and Italian dictionaries have key parity
        en_keys = set(TRANSLATIONS["en"].keys())
        it_keys = set(TRANSLATIONS["it"].keys())
        missing_in_it = en_keys - it_keys
        missing_in_en = it_keys - en_keys
        self.assertEqual(len(missing_in_it), 0, f"Keys missing in Italian: {missing_in_it}")
        self.assertEqual(len(missing_in_en), 0, f"Keys missing in English: {missing_in_en}")

    def test_translation_basic_and_fallback(self):
        # English lookup
        self.assertEqual(t("app_title", lang="en"), "QuakMeeting")
        self.assertEqual(t("banner_join_flight", lang="en"), "🚀 Join Flight")
        self.assertEqual(t("banner_got_it", lang="en"), "✅ Got it")

        # Italian lookup
        self.assertEqual(t("app_title", lang="it"), "QuakMeeting")
        self.assertEqual(t("banner_join_flight", lang="it"), "🚀 Entra nel Volo")
        self.assertEqual(t("banner_got_it", lang="it"), "✅ Capito")

        # Fallback to key if nonexistent
        self.assertEqual(t("nonexistent_key_123"), "nonexistent_key_123")

    def test_translation_interpolation(self):
        # English parameter formatting
        self.assertEqual(
            t("badge_in_mins_early", lang="en", mins=15),
            "In 15m • Early Alert"
        )
        self.assertEqual(
            t("badge_class_in_mins", lang="en", mins=10, classroom="Aula 5M"),
            "Lesson in 10m • Aula 5M"
        )

        # Italian parameter formatting
        self.assertEqual(
            t("badge_in_mins_early", lang="it", mins=15),
            "Tra 15m • Preavviso"
        )
        self.assertEqual(
            t("badge_class_in_mins", lang="it", mins=10, classroom="Aula 5M"),
            "Lezione tra 10m • Aula 5M"
        )

    def test_get_active_language(self):
        # Forced language
        self.assertEqual(get_active_language(forced_lang="it"), "it")
        self.assertEqual(get_active_language(forced_lang="en"), "en")

        # Default detection returns either 'it' or 'en'
        detected = detect_system_language()
        self.assertIn(detected, ["it", "en"])

if __name__ == "__main__":
    unittest.main()
