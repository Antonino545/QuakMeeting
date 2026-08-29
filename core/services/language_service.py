"""
Language and Internationalization Service for QuakMeeting.
Provides OS language detection, runtime language resolution, and bilingual translations (English & Italian).
"""
import os
import locale
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("QuakMeeting.LanguageService")

# Translation Dictionaries: English ('en') & Italian ('it')
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        # General & App
        "app_title": "QuakMeeting",
        "system_language": "System (Auto)",
        "language_en": "English 🇬🇧",
        "language_it": "Italiano 🇮🇹",
        "language_label": "Language / Lingua",
        "save": "Save",
        "saved": "Saved",
        "cancel": "Cancel",
        "close": "Close",
        "quit": "Quit QuakMeeting",
        "flight_deck": "Flight Deck",
        "preferences": "Flight Config...",
        "check_updates": "Check for Updates...",
        "no_events_today": "No events today",
        "all_caught_up": "All caught up! No more flights today.",
        "upcoming_alert": "Upcoming Alert",
        "test_banner": "Test Banner Alert",

        # Tray & Menu Bar
        "tray_all_day": "All Day",
        "tray_now": "NOW",
        "tray_in_mins": "in {mins}m",
        "tray_in_hours": "in {hours}h {mins}m",
        "tray_depart_in": "Leave in {mins}m",
        "tray_late": "LATE {mins}m",
        "tray_no_more": "No more flights today",
        "tray_calendar_sync": "Calendar Synced: {count} events",

        # Tabs
        "tab_agenda": "Flight Plan",
        "tab_hangar": "Pilot Hangar",
        "tab_settings": "Flight Config",

        # Agenda Tab
        "agenda_today_flights": "Today's Flights",
        "agenda_upcoming": "Upcoming Flights",
        "agenda_active": "In Flight Now",
        "agenda_completed": "Completed Flights",
        "agenda_no_flights": "No flights scheduled for today.",
        "agenda_join_button": "🚀 Join Flight",
        "agenda_maps_button": "🗺️ Directions",

        # Hangar Tab
        "hangar_title": "Pilot Hangar",
        "hangar_subtitle": "Select and customize your squad of flying mascots.",
        "hangar_default_pilot": "Default Mascot",
        "hangar_force_default": "Always use default mascot (disable smart classifier)",
        "hangar_active_badge": "ACTIVE PILOT",
        "hangar_select_btn": "Assign Pilot",
        "hangar_selected_btn": "✓ Current Pilot",
        "hangar_customize": "Customize Outfit",

        # Settings Tab
        "settings_general": "General Preferences",
        "settings_launch_at_login": "Launch at Login",
        "settings_sound": "Play Notification Sound",
        "settings_flight_speed": "Banner Flight Speed",
        "settings_status_mode": "Menu Bar Display Mode",
        "settings_status_countdown": "Dynamic Countdown (e.g. In 5m)",
        "settings_status_time": "Event Time (e.g. 14:30)",
        "settings_status_icon": "Icon Only",
        "settings_travel_eta": "Smart Travel & Multi-Modal Transit (Apple Maps)",
        "settings_home_address": "Home / Origin Address",
        "settings_transport_mode": "Preferred Transport Mode",
        "settings_transit": "Transit (Bus/Metro/Train) 🚆",
        "settings_driving": "Driving (Car) 🚗",
        "settings_walking": "Walking 🚶",
        "settings_cycling": "Cycling 🚲",
        "settings_eta_buffer": "Departure Buffer (Minutes)",
        "settings_calendars": "Connected Calendars",
        "settings_developer": "Developer & Diagnostic Tools",
        "settings_license": "📜 License & About",
        "license_title": "QuakMeeting License & Acknowledgements",
        "license_body": "QuakMeeting is free and open-source software licensed under the MIT License.\n\nAcknowledgements:\n• Inspired by QuakPit (Ooble Studio)\n• Palette & Visual Tokens: Catppuccin Mocha\n• Native Bridges: PyObjC & PyQt6\n• Calendar Sync: Apple EventKit & CalDAV (RFC 5545)",

        # Banner HUD & Buttons
        "banner_join_flight": "🚀 Join Flight",
        "banner_join_meeting": "🚀 Join Meeting",
        "banner_got_it": "✅ Got it",
        "banner_im_here": "📍 I'm Here",
        "banner_snooze_5m": "💤 5m",
        "banner_skip": "⏭️ Skip",
        "banner_online_meeting": "Online Meeting",

        # Banner Countdown & Badges
        "badge_in_mins_early": "In {mins}m • Early Alert",
        "badge_in_mins_ready": "In {mins}m • Get Ready",
        "badge_in_mins_almost": "In {mins}m • Almost Time!",
        "badge_in_secs_now": "In {secs}s • Starting Now!",
        "badge_study_in_mins": "In {mins}m • Study Time",
        "badge_study_open_books": "In {mins}m • Open Books",
        "badge_study_time_to_study": "In {mins}m • Time to Study!",
        "badge_study_starting": "In {secs}s • Study Starting!",
        "badge_class_in_mins": "Lesson in {mins}m • {classroom}",
        "badge_class_soon": "Class in {mins}m • {classroom}",
        "badge_class_starting": "Class starting now • {classroom}",
        "badge_travel_in_mins": "In {mins}m • Travel Notice",
        "badge_travel_prepare": "In {mins}m • Prepare to Leave",
        "badge_travel_leave_now": "Leave Now!",
        "badge_travel_leave_in": "Leave in {mins}m ({time})",
        "badge_travel_leave_at": "Leave at {time} (~{duration})",
        "badge_travel_late_by": "LATE BY {mins}m • LEAVE NOW!",
        "badge_travel_depart_now": "DEPART NOW!",
        "badge_late_by_mins": "LATE BY {mins}m • IN PROGRESS",
        "badge_late_class_by": "LATE BY {mins}m • {classroom}",
        "badge_late_study_by": "STUDY OVERDUE BY {mins}m • DO IT!",
        "badge_in_progress": "IN PROGRESS NOW",
        "badge_class_started": "CLASS STARTED • {classroom}",
        "badge_study_now": "TIME TO STUDY • DO IT!",

        # Event Providers & Titles
        "provider_study": "Study Session 📖",
        "provider_class": "University Lecture 🎓",
        "provider_food": "Dinner / Food 🍕🍽️",
        "provider_travel": "Travel & Transit ✈️🚆",
        "provider_gym": "Workout & Fitness 🏋️‍♂️",
        "provider_health": "Wellness & Health 🧘",
        "provider_in_person": "Appointment / Errand 📍",
        "provider_quick": "Quick Sync / Brainstorm 🐿️",
        "provider_calendar": "Calendar Alert ⏰"
    },

    "it": {
        # General & App
        "app_title": "QuakMeeting",
        "system_language": "Sistema (Auto)",
        "language_en": "English 🇬🇧",
        "language_it": "Italiano 🇮🇹",
        "language_label": "Lingua / Language",
        "save": "Salva",
        "saved": "Salvato",
        "cancel": "Annulla",
        "close": "Chiudi",
        "quit": "Esci da QuakMeeting",
        "flight_deck": "Flight Deck",
        "preferences": "Configurazione Volo...",
        "check_updates": "Verifica Aggiornamenti...",
        "no_events_today": "Nessun evento oggi",
        "all_caught_up": "Tutto completato! Nessun altro volo in programma oggi.",
        "upcoming_alert": "Avviso Prossimo Volo",
        "test_banner": "Avviso Banner di Prova",

        # Tray & Menu Bar
        "tray_all_day": "Tutto il giorno",
        "tray_now": "ORA",
        "tray_in_mins": "tra {mins}m",
        "tray_in_hours": "tra {hours}h {mins}m",
        "tray_depart_in": "Partenza tra {mins}m",
        "tray_late": "RITARDO {mins}m",
        "tray_no_more": "Nessun altro volo oggi",
        "tray_calendar_sync": "Calendario sincronizzato: {count} eventi",

        # Tabs
        "tab_agenda": "Piano di Volo",
        "tab_hangar": "Hangar Piloti",
        "tab_settings": "Configurazione",

        # Agenda Tab
        "agenda_today_flights": "Voli di Oggi",
        "agenda_upcoming": "Prossimi Voli",
        "agenda_active": "In Volo Adesso",
        "agenda_completed": "Voli Completati",
        "agenda_no_flights": "Nessun volo in programma per oggi.",
        "agenda_join_button": "🚀 Entra nel Volo",
        "agenda_maps_button": "🗺️ Indicazioni Mappe",

        # Hangar Tab
        "hangar_title": "Hangar Piloti",
        "hangar_subtitle": "Seleziona e personalizza la tua squadriglia di mascotte volanti.",
        "hangar_default_pilot": "Mascotte Predefinita",
        "hangar_force_default": "Usa sempre la mascotte predefinita (disattiva classificazione automatica)",
        "hangar_active_badge": "PILOTA ATTIVO",
        "hangar_select_btn": "Assegna Pilota",
        "hangar_selected_btn": "✓ Pilota Attuale",
        "hangar_customize": "Personalizza Completo",

        # Settings Tab
        "settings_general": "Preferenze Generali",
        "settings_launch_at_login": "Avvia al login di sistema",
        "settings_sound": "Riproduci suono di notifica",
        "settings_flight_speed": "Velocità di volo del banner",
        "settings_status_mode": "Modalità icona barra dei menu",
        "settings_status_countdown": "Conto alla rovescia dinamico (es. Tra 5m)",
        "settings_status_time": "Orario evento (es. 14:30)",
        "settings_status_icon": "Solo Icona",
        "settings_travel_eta": "Calcolo Spostamenti & Mezzi (Apple Maps)",
        "settings_home_address": "Indirizzo di partenza / Casa",
        "settings_transport_mode": "Mezzo di trasporto preferito",
        "settings_transit": "Mezzi Pubblici (Bus/Metro/Treno) 🚆",
        "settings_driving": "Automobile 🚗",
        "settings_walking": "A Piedi 🚶",
        "settings_cycling": "Bicicletta 🚲",
        "settings_eta_buffer": "Margine di anticipo partenza (minuti)",
        "settings_calendars": "Calendari Collegati",
        "settings_developer": "Strumenti Sviluppatore & Diagnostica",
        "settings_license": "📜 Licenza e Info",
        "license_title": "Licenza e Ringraziamenti di QuakMeeting",
        "license_body": "QuakMeeting è un software libero e open-source distribuito con licenza MIT.\n\nRingraziamenti:\n• Ispirato da QuakPit (Ooble Studio)\n• Palette e Design: Catppuccin Mocha\n• Integrazioni native: PyObjC e PyQt6\n• Sincronizzazione calendari: Apple EventKit e CalDAV (RFC 5545)",

        # Banner HUD & Buttons
        "banner_join_flight": "🚀 Entra nel Volo",
        "banner_join_meeting": "🚀 Partecipa alla Riunione",
        "banner_got_it": "✅ Capito",
        "banner_im_here": "📍 Sono qui",
        "banner_snooze_5m": "💤 5m",
        "banner_skip": "⏭️ Salta",
        "banner_online_meeting": "Riunione Online",

        # Banner Countdown & Badges
        "badge_in_mins_early": "Tra {mins}m • Preavviso",
        "badge_in_mins_ready": "Tra {mins}m • Preparati",
        "badge_in_mins_almost": "Tra {mins}m • Quasi ora!",
        "badge_in_secs_now": "Tra {secs}s • Inizio ora!",
        "badge_study_in_mins": "Tra {mins}m • Studio",
        "badge_study_open_books": "Tra {mins}m • Apri i Libri",
        "badge_study_time_to_study": "Tra {mins}m • Tempo di Studiare!",
        "badge_study_starting": "Tra {secs}s • Studio al via!",
        "badge_class_in_mins": "Lezione tra {mins}m • {classroom}",
        "badge_class_soon": "Classe tra {mins}m • {classroom}",
        "badge_class_starting": "Lezione al via • {classroom}",
        "badge_travel_in_mins": "Tra {mins}m • Avviso Partenza",
        "badge_travel_prepare": "Tra {mins}m • Preparati a uscire",
        "badge_travel_leave_now": "Esci Adesso!",
        "badge_travel_leave_in": "Partenza tra {mins}m ({time})",
        "badge_travel_leave_at": "Partenza alle {time} (~{duration})",
        "badge_travel_late_by": "IN RITARDO DI {mins}m • ESCI ORA!",
        "badge_travel_depart_now": "PARTENZA ORA!",
        "badge_late_by_mins": "IN RITARDO DI {mins}m • IN CORSO",
        "badge_late_class_by": "IN RITARDO DI {mins}m • {classroom}",
        "badge_late_study_by": "STUDIO IN RITARDO DI {mins}m • STUDIA!",
        "badge_in_progress": "IN CORSO ORA",
        "badge_class_started": "LEZIONE INIZIATA • {classroom}",
        "badge_study_now": "TEMPO DI STUDIARE • FALLO ORA!",

        # Event Providers & Titles
        "provider_study": "Sessione di Studio 📖",
        "provider_class": "Lezione Universitaria 🎓",
        "provider_food": "Cena / Pranzo 🍕🍽️",
        "provider_travel": "Viaggio & Spostamento ✈️🚆",
        "provider_gym": "Allenamento & Fitness 🏋️‍♂️",
        "provider_health": "Salute & Benessere 🧘",
        "provider_in_person": "Appuntamento / Visita 📍",
        "provider_quick": "Confronto Veloce / Idea 🐿️",
        "provider_calendar": "Avviso Calendario ⏰"
    }
}


def detect_system_language() -> str:
    """Detects the operating system's preferred language code ('it' or 'en')."""
    # 1. macOS native preferred language detection via PyObjC
    try:
        import AppKit
        langs = AppKit.NSLocale.preferredLanguages()
        if langs and len(langs) > 0:
            primary = str(langs[0]).lower()
            if primary.startswith("it"):
                return "it"
            return "en"
    except Exception:
        pass

    # 2. Linux environment / locale detection
    for env_var in ["LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"]:
        val = os.environ.get(env_var)
        if val:
            val_low = val.lower()
            if val_low.startswith("it") or "it_" in val_low or "it-" in val_low:
                return "it"
            if val_low.startswith("en") or "en_" in val_low or "en-" in val_low:
                return "en"

    # 3. Python standard locale
    try:
        loc = locale.getlocale()
        if loc and loc[0]:
            if loc[0].lower().startswith("it"):
                return "it"
    except Exception:
        pass

    return "en"


def get_active_language(forced_lang: Optional[str] = None) -> str:
    """Resolves the current active language ('en' or 'it') taking user config into account."""
    if forced_lang and forced_lang in ("en", "it"):
        return forced_lang

    try:
        from core.services.config_service import config
        configured = str(config.get("language", "system")).lower()
        if configured in ("it", "italian", "italiano"):
            return "it"
        if configured in ("en", "english"):
            return "en"
    except Exception:
        pass

    return detect_system_language()


def t(key: str, lang: Optional[str] = None, **kwargs) -> str:
    """Translates a key into the active language with optional parameter interpolation."""
    active_lang = lang or get_active_language()
    dict_for_lang = TRANSLATIONS.get(active_lang) or TRANSLATIONS["en"]

    template = dict_for_lang.get(key)
    if template is None:
        template = TRANSLATIONS["en"].get(key, key)

    if kwargs:
        try:
            return template.format(**kwargs)
        except Exception:
            return template

    return template
