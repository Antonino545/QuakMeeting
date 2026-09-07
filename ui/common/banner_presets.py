"""
Shared Banner Presets for QuakMeeting.
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


def get_update_preset(version_str: str = "New Version", release_url: str = "") -> Dict[str, Any]:
    """Generates banner payload for QuakMeeting software updates."""
    return {
        "title": f"QuakMeeting {version_str} Ready!",
        "provider": "Software Update ✨",
        "pilot_type": "captain",
        "action_btn_text": "⚡ UPDATE NOW",
        "quote_text": f"🚀 {version_str} IS READY!",
        "action_url": release_url or "https://github.com/Antonino545/QuakMeeting/releases",
        "start_time": datetime.now().astimezone(),
        "is_travel": False,
        "is_update_banner": True,
        "location": "Click to download & install update",
    }
