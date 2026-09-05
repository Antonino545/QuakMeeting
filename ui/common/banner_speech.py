"""
Common Pilot Speech Generation for QuakMeeting Banners.
Provides animal-specific vocalizations and context-aware quotes across macOS & Linux in English & Italian.
"""
from typing import Dict, Any, Optional
from core.services.language_service import get_active_language

def build_pilot_speech_text(
    meeting_data: Dict[str, Any],
    animal: Optional[str] = None,
    outfit: Optional[str] = None,
    pilot_type: Optional[str] = None,
    is_late: bool = False,
    classroom: Optional[str] = None,
    title: Optional[str] = None,
    provider: Optional[str] = None,
    lang: Optional[str] = None,
    reminder_stage: Optional[int] = None
) -> str:
    """Constructs animal-aware, context-aware quote for the pilot speech bubble."""
    active_lang = lang or get_active_language()
    stage = reminder_stage if reminder_stage is not None else meeting_data.get("reminder_stage")

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
        or meeting_data.get("category") == "study"
        or "STUDY" in (provider or "").upper()
        or "STUDIARE" in (title or "").upper()
        or "STUDIO" in (title or "").upper()
        or "STUDY" in (title or "").upper()
        or "SELF STUDY" in (title or "").upper()
        or "SELF-STUDY" in (title or "").upper()
        or "RIPASSO" in (title or "").upper()
        or "COMPITI" in (title or "").upper()
        or "HOMEWORK" in (title or "").upper()
    )

    if active_lang == "it":
        if is_late:
            if chosen_animal == "owl":
                if is_self_study:
                    return "HOOOT! 🚨 DEVI STUDIARE! FALLO ORA! 📖"
                if classroom:
                    return f"HOOOT! 🚨 LEZIONE INIZIATA IN {classroom.upper()}! CORRI!"
                return "HOOOT! 🚨 IL PROFESSORE STA INIZIANDO! SEI IN RITARDO!"
            elif chosen_animal == "bunny":
                if chosen_outfit == "gym":
                    return "BOING! 🔥 NON SALTARE L'ALLENAMENTO! TEMPO DI GHISA! 🏋️‍♂️"
                if is_self_study:
                    return "HOP-HOP! 🚨 SESSIONE DI STUDIO INIZIATA! SCATTA! 📖"
                if chosen_outfit == "chef":
                    return "HOP-HOP! 🔥 IL CIBO SI RAFFREDDA! CORRI! 🍕"
                return "HOP-HOP! 🚨 SEI IN RITARDO! SALTA AL VOLO! 🐰💨"
            elif chosen_animal == "squirrel":
                if chosen_outfit in ("driver", "racer"):
                    return "CHIRP! 🔥 GIÙ IL PIEDE SULL'ACCELERATORE! SIAMO IN RITARDO! 🏎️"
                return "CHIRP-CHIRP! 🚨 ALLARME ROTTA! SEI IN RITARDO! SCATTA! 🐿️⚡"
            elif chosen_animal == "platypus":
                return "KK-KK-KK-KK! 🚨 MISSIONE A RISCHIO! SCATTA AGENTE P! 🕵️‍♂️💨"
            else: # Duck
                if chosen_outfit == "chef":
                    return "QUAK! 🔥 IL CIBO SI RAFFREDDA! SBRIGATI! 🍕"
                elif chosen_outfit == "captain":
                    return "QUAK! ⚠️ ULTIMA CHIAMATA IMBARCO! CORRI AL GATE! ✈️"
                elif chosen_outfit in ("driver", "racer"):
                    return "QUAK! 🔥 ACCELERA! SIAMO IN RITARDO! 🏎️"
                elif chosen_outfit == "gym":
                    return "QUAK! 🔥 NON SALTARE L'ALLENAMENTO! TEMPO DI GHISA! 🏋️‍♂️"
                elif chosen_outfit == "zen":
                    return "QUAK! 🚨 RESPIRA... E SCATTA! 🏃💨"
                elif is_self_study:
                    return "QUAAK! 🚨 DEVI STUDIARE! FALLO ORA! 📖"
                return "QUAAK! 🚨 SEI IN RITARDO! CORRI! 🦆"
        else:
            if stage is not None and stage > 0:
                if chosen_animal == "owl":
                    if is_self_study:
                        return "Hoot! Preavviso studio al volo! 📖✈️"
                    if classroom:
                        return f"Hoot! Preavviso: lezione in {classroom}! 📚✈️"
                    return "Hoot! Preavviso al volo! 🦉✈️"
                elif chosen_animal == "bunny":
                    if chosen_outfit == "gym":
                        return "Boing! Preavviso allenamento al volo! 🏋️‍♂️✈️"
                    if is_self_study:
                        return "Hop-hop! Preavviso studio al volo! 📖✈️"
                    if chosen_outfit == "chef":
                        return "Hop-hop! Preavviso: cibo in arrivo! 🍕✈️"
                    return "Hop-hop! Preavviso al volo! 🐰✈️"
                elif chosen_animal == "squirrel":
                    if chosen_outfit in ("driver", "racer"):
                        return "Chirp-chirp! Sorvolo rapido: prepararsi! 🏎️💨"
                    return "Chirp! Preavviso rapido al volo! 🐿️⚡"
                elif chosen_animal == "platypus":
                    return "Kk-kk-kk! (Sorvolo di ricognizione... 🕵️‍♂️✈️)"
                else: # Duck
                    if chosen_outfit == "chef":
                        return "Quak! Preavviso: cibo tra poco! 🍕✈️"
                    if is_self_study:
                        return "Quak! Preavviso: studio tra poco! 📖✈️"
                    if chosen_outfit == "gym":
                        return "Quak! Preavviso: allenamento a breve! 🏋️‍♂️✈️"
                    return "Quak! Preavviso al volo! 🦆✈️"

            if chosen_animal == "owl":
                if is_self_study:
                    return "Hoot! Tempo di studio! Apri i libri e studia! 📖"
                if classroom:
                    return f"Hoot! Lezione in {classroom} a breve! 📚"
                if chosen_outfit == "chef":
                    return "Hoot! Pranzo / Cena gourmet a breve! 🍕"
                if chosen_outfit == "captain":
                    return "Hoot! Decollo del volo in avvicinamento ✈️"
                return "Hoot! Lezione al via tra poco! 🦉"
            elif chosen_animal == "bunny":
                if chosen_outfit == "gym":
                    return "Boing! Tempo di spingere e allenarsi! 🏋️‍♂️💪"
                if chosen_outfit == "zen":
                    return "Hop! Respiro calmo, benessere e relax 🌸"
                if chosen_outfit == "chef":
                    return "Hop-hop! Banchetto gourmet in arrivo! 🍕"
                if is_self_study:
                    return "Hop-hop! Studio sprint! Massima concentrazione! 📖"
                if chosen_outfit == "captain":
                    return "Hop-hop! Pronti per il decollo! ✈️"
                return "Hop-hop! Diamoci una mossa! 🐰"
            elif chosen_animal == "squirrel":
                if chosen_outfit in ("driver", "racer"):
                    return "Chirp-chirp! Rotta veloce impostata! 🏎️💨"
                if chosen_outfit == "gym":
                    return "Nut-ping! Workout ad alto voltaggio! 🏋️⚡"
                if is_self_study:
                    return "Chirp-chirp! Sessione di studio lampo! 🌰📖"
                if chosen_outfit == "chef":
                    return "Chirp! Spuntino e cibo pronti! 🍕"
                return "Nut-ping! Pronti all'azione! 🐿️🌰"
            elif chosen_animal == "platypus":
                if is_self_study:
                    return "Kk-kk-kk! (Operazione studio in incognito! 📖)"
                if chosen_outfit == "gym":
                    return "Kk-kk! (Addestramento tattico in corso! 🏋️‍♂️)"
                return "Kk-kk-kk-kk! (Briefing Missione Segreta! 🕵️‍♂️)"
            else: # Duck
                if chosen_outfit == "chef":
                    return "Quak! Pranzo / cena a breve! 🍕"
                elif chosen_outfit == "captain":
                    return "Quak! Equipaggio, prepararsi al decollo ✈️"
                elif chosen_outfit in ("driver", "racer"):
                    return "Quak! Motori accesi, pronti a partire! 🏎️"
                elif chosen_outfit == "gym":
                    return "Quak! Tempo di allenamento e ghisa! 🏋️‍♂️💪"
                elif chosen_outfit == "zen":
                    return "Quak! Momento di calma e benessere 🌸"
                elif is_self_study:
                    return "Quak! Tempo di studiare! Apri i libri! 📖"
                return "Quak! Pronti al decollo! 🦆"
    else: # English (Default)
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
            if stage is not None and stage > 0:
                if chosen_animal == "owl":
                    if is_self_study:
                        return "Hoot! Heads up study preview! 📖✈️"
                    if classroom:
                        return f"Hoot! Heads up: class in {classroom}! 📚✈️"
                    return "Hoot! Heads up! Just flying by! 🦉✈️"
                elif chosen_animal == "bunny":
                    if chosen_outfit == "gym":
                        return "Boing! Heads up: workout soon! 🏋️‍♂️✈️"
                    if is_self_study:
                        return "Hop-hop! Heads up study sprint soon! 📖✈️"
                    if chosen_outfit == "chef":
                        return "Hop-hop! Heads up: dining time soon! 🍕✈️"
                    return "Hop-hop! Heads up! Just flying by! 🐰✈️"
                elif chosen_animal == "squirrel":
                    if chosen_outfit in ("driver", "racer"):
                        return "Chirp-chirp! Flyby preview: ready to roll! 🏎️💨"
                    return "Chirp! Quick heads-up flyby! 🐿️⚡"
                elif chosen_animal == "platypus":
                    return "Kk-kk-kk! (Recon flyby in progress... 🕵️‍♂️✈️)"
                else: # Duck
                    if chosen_outfit == "chef":
                        return "Quak! Heads up: dining time soon! 🍕✈️"
                    if is_self_study:
                        return "Quak! Heads up: study time soon! 📖✈️"
                    if chosen_outfit == "gym":
                        return "Quak! Heads up: workout coming up! 🏋️‍♂️✈️"
                    return "Quak! Heads up! Just flying by! 🦆✈️"

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


def build_pilot_hover_speech_text(animal: Optional[str] = None, lang: Optional[str] = None) -> str:
    """Returns a fun, animal-specific quote when the cursor hovers over the mascot."""
    active_lang = lang or get_active_language()
    chosen_animal = (animal or "duck").lower()

    if active_lang == "it":
        if chosen_animal == "owl":
            return "Uhu! Osservo dall'alto! 🦉✨"
        elif chosen_animal == "bunny":
            return "Hop! Fermo a mezz'aria! 🐰✨"
        elif chosen_animal == "squirrel":
            return "Squit! Metto il tempo da parte! 🐿️"
        elif chosen_animal == "platypus":
            return "Kk-kk! (Planata silenziosa!) 🦆🏊"
        else:
            return "Quak! Modalità stazionaria attiva! 🛸"
    else:
        if chosen_animal == "owl":
            return "Hoo! Observing from above! 🦉✨"
        elif chosen_animal == "bunny":
            return "Hop! Paused in mid-air! 🐰✨"
        elif chosen_animal == "squirrel":
            return "Squeak! Stashing time! 🐿️"
        elif chosen_animal == "platypus":
            return "Kk-kk! (Gliding silently!) 🦆🏊"
        else:
            return "Quak! Hover mode engaged! 🛸"

