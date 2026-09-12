"""
Shared Banner Presets for FlightDeck.
Provides cross-platform mock meeting payloads for mascot test flights
and software update banner notifications.
"""
from datetime import datetime
from typing import Dict, Any


def get_test_preset(pilot_type: str) -> Dict[str, Any]:
    """Generates mock meeting payload for simulating a flight banner test."""
    presets = {
        "duck": {
            "title": "Weekly Team Sync (Google Meet)",
            "provider": "Google Meet 🟢",
            "pilot_type": "duck",
            "action_btn_text": "🚀 JOIN GOOGLE MEET",
            "action_url": "https://meet.google.com/test-quak-pit",
            "start_time": datetime.now().astimezone(),
            "is_travel": False
        },
        "chef": {
            "title": "Dinner with Friends at Pizzeria",
            "provider": "Dinner / Food 🍕🍽️",
            "pilot_type": "chef",
            "action_btn_text": "🗺️ RESTAURANT DIRECTIONS",
            "action_url": "https://maps.apple.com/?q=Pizzeria+Napoli",
            "location": "Pizzeria Da Michele",
            "travel_time_minutes": 25,
            "transport_mode": "transit",
            "start_time": datetime.now().astimezone(),
            "is_travel": True
        },
        "captain": {
            "title": "Flight to London (BA 257)",
            "provider": "Flight / Travel ✈️",
            "pilot_type": "captain",
            "action_btn_text": "🗺️ AIRPORT DIRECTIONS",
            "action_url": "https://maps.apple.com/?q=Heathrow+Airport",
            "location": "Terminal 5 - Gate B12",
            "travel_time_minutes": 45,
            "transport_mode": "driving",
            "start_time": datetime.now().astimezone(),
            "is_travel": True
        },
        "owl": {
            "title": "SmartGrid & Neural Networks Lecture",
            "provider": "Study / University 🎓",
            "pilot_type": "owl",
            "action_btn_text": "📚 CLASSROOM & NOTES",
            "action_url": "https://calendar.apple.com",
            "classroom": "Room 3B - Campus",
            "teacher": "Prof. Smith",
            "location": "Room 3B - Campus",
            "start_time": datetime.now().astimezone(),
            "is_travel": False
        },
        "gym": {
            "title": "CrossFit Training & Palestra Workout",
            "provider": "Gym & Sport 🏋️‍♂️💪",
            "pilot_type": "gym",
            "action_btn_text": "🗺️ GYM DIRECTIONS",
            "action_url": "https://maps.apple.com/?daddr=Gym+Fitness",
            "location": "Downtown Gym Club",
            "travel_time_minutes": 15,
            "transport_mode": "bicycling",
            "start_time": datetime.now().astimezone(),
            "is_travel": True
        },
        "driver": {
            "title": "Architecture Studio Meeting",
            "provider": "In Person 📍 Travel Time!",
            "pilot_type": "driver",
            "action_btn_text": "🗺️ NAVIGATE WITH MAPS",
            "action_url": "https://maps.apple.com/?daddr=City+Center",
            "location": "Victoria Street, London",
            "travel_time_minutes": 30,
            "transport_mode": "driving",
            "start_time": datetime.now().astimezone(),
            "is_travel": True
        },
        "zen_duck": {
            "title": "Serenis Online Therapy Session",
            "provider": "Serenis 🛋️",
            "pilot_type": "zen_duck",
            "action_btn_text": "🚀 JOIN SESSION",
            "action_url": "https://app.serenis.it/join/test",
            "start_time": datetime.now().astimezone(),
            "is_travel": False
        },
        "platypus": {
            "title": "Top Secret Agent Mission Briefing",
            "provider": "Secret Mission 🕵️‍♂️",
            "pilot_type": "platypus",
            "action_btn_text": "🔍 TOP SECRET BRIEFING",
            "action_url": "https://calendar.apple.com",
            "start_time": datetime.now().astimezone(),
            "is_travel": False
        },
        "squirrel": {
            "title": "Sprint Planning & Quick Sync",
            "provider": "Quick Sync 🐿️⚡",
            "pilot_type": "squirrel",
            "action_btn_text": "⚡ JOIN QUICK SYNC",
            "action_url": "https://calendar.apple.com",
            "start_time": datetime.now().astimezone(),
            "is_travel": False
        }
    }
    return presets.get(pilot_type, presets["duck"])


from core.services.language_service import t


def get_update_preset(version_str: str = "New Version", release_url: str = "") -> Dict[str, Any]:
    """Generates banner payload for FlightDeck software updates."""
    return {
        "title": f"FlightDeck {version_str} Ready!",
        "provider": "Software Update ✨",
        "subtitle": "⚡ Ready to download & install update",
        "pilot_type": "captain",
        "action_btn_text": "⚡ UPDATE NOW",
        "quote_text": f"🚀 {version_str} IS READY!",
        "action_url": release_url or "https://github.com/Antonino545/FlightDeck/releases",
        "start_time": datetime.now().astimezone(),
        "is_travel": False,
        "is_update_banner": True,
        "is_up_to_date": False,
        "location": "Click to download & install update",
    }


def get_up_to_date_preset(version_str: str = "") -> Dict[str, Any]:
    """Generates modular banner payload when FlightDeck is already on the latest version."""
    v = version_str or "v1.0.0"
    if not v.startswith("v"):
        v = f"v{v}"
    title_str = t("update_up_to_date_title")
    title = title_str if title_str != "update_up_to_date_title" else "You're Up to Date! ✨"
    pill_str = t("update_up_to_date_pill")
    provider = pill_str if pill_str != "update_up_to_date_pill" else "UP TO DATE ✨"
    sub_str = t("update_up_to_date_sub", version=v)
    sub = sub_str if sub_str != "update_up_to_date_sub" else f"FlightDeck {v} is currently the newest version."
    btn_str = t("update_up_to_date_btn")
    btn = btn_str if btn_str != "update_up_to_date_btn" else "✓ Great"

    return {
        "title": title,
        "provider": provider,
        "subtitle": sub,
        "pilot_type": "captain",
        "action_btn_text": btn,
        "quote_text": f"✨ {v} is the latest version!",
        "action_url": "",
        "start_time": datetime.now().astimezone(),
        "is_travel": False,
        "is_update_banner": True,
        "is_up_to_date": True,
        "location": "",
    }


def get_update_error_preset(error_msg: str = "") -> Dict[str, Any]:
    """Generates modular banner payload when update check fails during manual request."""
    title_str = t("update_check_failed_title")
    title = title_str if title_str != "update_check_failed_title" else "Update Check Failed"
    sub_str = t("update_check_failed_sub")
    sub = error_msg or (sub_str if sub_str != "update_check_failed_sub" else "Could not connect to GitHub Releases.")

    return {
        "title": title,
        "provider": "Software Update ⚠️",
        "subtitle": sub,
        "pilot_type": "captain",
        "action_btn_text": "✕ Dismiss",
        "quote_text": "Could not check for updates",
        "action_url": "",
        "start_time": datetime.now().astimezone(),
        "is_travel": False,
        "is_update_banner": True,
        "is_up_to_date": False,
        "is_update_error": True,
        "location": "",
    }

