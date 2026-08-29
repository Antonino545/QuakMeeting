"""
Common Pilot Speech Generation for QuakMeeting Banners.
Provides animal-specific vocalizations and context-aware quotes across macOS & Linux.
"""
from typing import Dict, Any, Optional

def build_pilot_speech_text(
    meeting_data: Dict[str, Any],
    animal: Optional[str] = None,
    outfit: Optional[str] = None,
    pilot_type: Optional[str] = None,
    is_late: bool = False,
    classroom: Optional[str] = None,
    title: Optional[str] = None,
    provider: Optional[str] = None
) -> str:
    """Constructs animal-aware, context-aware quote for the pilot speech bubble."""
    chosen_animal = animal
    if not chosen_animal:
        if pilot_type in ("owl", "platypus", "squirrel", "bunny"):
            chosen_animal = pilot_type
        else:
            chosen_animal = "duck"

    chosen_outfit = (outfit or pilot_type or "aviator").lower()
    chosen_animal = chosen_animal.lower()

    is_self_study = (
        meeting_data.get("event_type") == "study"
        or "STUDY" in (provider or "").upper()
        or "STUDIARE" in (title or "").upper()
        or (not classroom and "STUDY" in (title or "").upper())
    )

    if is_late:
        if chosen_animal == "owl":
            if is_self_study:
                return "HOOOT! 🚨 YOU NEED TO STUDY! DO IT! 📖"
            if classroom:
                return f"HOOOT! 🚨 CLASS STARTED IN {classroom.upper()}! SPRINT!"
            return "HOOOT! 🚨 PROFESSOR IS STARTING! YOU'RE LATE!"
        elif chosen_animal == "bunny":
            if chosen_outfit == "gym":
                return "BOING! 🔥 DON'T SKIP WORKOUT! TIME FOR GAINS! 🏋️‍♂️"
            if is_self_study:
                return "HOP-HOP! 🚨 STUDY SESSION STARTED! SPRINT! 📖"
            if chosen_outfit == "chef":
                return "HOP-HOP! 🔥 FOOD IS GETTING COLD! SPRINT! 🍕"
            return "HOP-HOP! 🚨 YOU ARE LATE! HOP TO IT! 🐰💨"
        elif chosen_animal == "squirrel":
            if chosen_outfit in ("driver", "racer"):
                return "CHIRP! 🔥 FLOOR THE GAS! WE ARE LATE! 🏎️"
            return "CHIRP-CHIRP! 🚨 NUT-PING ALERT! YOU'RE LATE! SPRINT! 🐿️⚡"
        elif chosen_animal == "platypus":
            return "KK-KK-KK-KK! 🚨 MISSION AT RISK! SPRINT AGENT P! 🕵️‍♂️💨"
        else: # Duck
            if chosen_outfit == "chef":
                return "QUAK! 🔥 THE FOOD IS GETTING COLD! HURRY! 🍕"
            elif chosen_outfit == "captain":
                return "QUAK! ⚠️ LAST CALL FOR BOARDING! SPRINT TO GATE! ✈️"
            elif chosen_outfit in ("driver", "racer"):
                return "QUAK! 🔥 FLOOR THE GAS! WE ARE LATE! 🏎️"
            elif chosen_outfit == "gym":
                return "QUAK! 🔥 DON'T SKIP WORKOUT! TIME FOR GAINS! 🏋️‍♂️"
            elif chosen_outfit == "zen":
                return "QUAK! 🚨 BREATHE IN... AND SPRINT! 🏃💨"
            elif is_self_study:
                return "QUAAK! 🚨 YOU NEED TO STUDY! DO IT! 📖"
            return "QUAAK! 🚨 YOU ARE LATE! RUN! 🦆"
    else:
        if chosen_animal == "owl":
            if is_self_study:
                return "Hoot! Time to study! You need to study, do it! 📖"
            if classroom:
                return f"Hoot! Class in {classroom} soon! 📚"
            if chosen_outfit == "chef":
                return "Hoot! Gourmet dining time soon! 🍕"
            if chosen_outfit == "captain":
                return "Hoot! Flight departure approaching ✈️"
            return "Hoot! Class starting soon! 🦉"
        elif chosen_animal == "bunny":
            if chosen_outfit == "gym":
                return "Boing! Time to train & crush workout! 🏋️‍♂️💪"
            if chosen_outfit == "zen":
                return "Hop! Soft breaths, wellness & calm 🌸"
            if chosen_outfit == "chef":
                return "Hop-hop! Fresh gourmet feast soon! 🍕"
            if is_self_study:
                return "Hop-hop! Study sprint time! Focus! 📖"
            if chosen_outfit == "captain":
                return "Hop-hop! Ready for takeoff! ✈️"
            return "Hop-hop! Let's get moving! 🐰"
        elif chosen_animal == "squirrel":
            if chosen_outfit in ("driver", "racer"):
                return "Chirp-chirp! Speedy route locked in! 🏎️💨"
            if chosen_outfit == "gym":
                return "Nut-ping! High voltage workout time! 🏋️⚡"
            if is_self_study:
                return "Chirp-chirp! Lightning study session! 🌰📖"
            if chosen_outfit == "chef":
                return "Chirp! Snack time & dinner ready! 🍕"
            return "Nut-ping! Ready for action! 🐿️🌰"
        elif chosen_animal == "platypus":
            if is_self_study:
                return "Kk-kk-kk! (Undercover study operation! 📖)"
            if chosen_outfit == "gym":
                return "Kk-kk! (Tactical physical training! 🏋️‍♂️)"
            return "Kk-kk-kk-kk! (Secret Mission Briefing! 🕵️‍♂️)"
        else: # Duck
            if chosen_outfit == "chef":
                return "Quak! Dinner / food time soon! 🍕"
            elif chosen_outfit == "captain":
                return "Quak! Cabin crew, prepare for takeoff ✈️"
            elif chosen_outfit in ("driver", "racer"):
                return "Quak! Engines running, ready to roll! 🏎️"
            elif chosen_outfit == "gym":
                return "Quak! Time to train & crush workout! 🏋️‍♂️💪"
            elif chosen_outfit == "zen":
                return "Quak! Time for wellness & calm 🌸"
            elif is_self_study:
                return "Quak! Time to study! Open the books! 📖"
            return "Quak! Ready for takeoff! 🦆"
