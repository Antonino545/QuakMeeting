import subprocess
import re
import urllib.parse
from datetime import datetime, timedelta
from config_manager import config

# Patterns per identificare i link di videochiamata
MEETING_PATTERNS = [
    r'https?://meet\.google\.com/[a-z0-9-]+',
    r'https?://[a-z0-9-]+\.zoom\.us/j/[0-9]+[^\s"\'<>]*',
    r'https?://teams\.microsoft\.com/[^\s"\'<>]+',
    r'https?://teams\.live\.com/[^\s"\'<>]+',
    r'https?://[a-z0-9-]+\.webex\.com/[^\s"\'<>]+',
    r'https?://meet\.jit\.si/[^\s"\'<>]+',
    r'https?://whereby\.com/[^\s"\'<>]+',
    r'https?://(?:app\.)?serenis\.it/join/[a-zA-Z0-9_-]+',
    r'https?://[^\s"\'<>]+(?:meeting|join|call|vc)[^\s"\'<>]*'
]

def extract_meeting_url(text):
    if not text or text == 'missing value':
        return None
    for pattern in MEETING_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            url = match.group(0).rstrip('.,;)')
            return url
    return None

def parse_applescript_date(date_str):
    if not date_str or date_str == 'missing value':
        return None
    
    formats = [
        "%A, %d %B %Y at %H:%M:%S",
        "%A %d %B %Y %H:%M:%S",
        "%d %B %Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S"
    ]
    
    clean_str = date_str.replace(" alle ", " ").replace(" at ", " ")
    for fmt in formats:
        try:
            return datetime.strptime(clean_str, fmt)
        except ValueError:
            pass

    try:
        time_match = re.search(r'(\d{1,2}):(\d{2}):(\d{2})', date_str)
        if time_match:
            h, m, s = map(int, time_match.groups())
            now = datetime.now()
            day_match = re.search(r'\b(\d{1,2})\b', date_str)
            day = int(day_match.group(1)) if day_match else now.day
            return datetime(now.year, now.month, day, h, m, s)
    except Exception:
        pass
        
    return None

def classify_event(title, location, desc, meeting_url):
    """Classifica l'evento in base al titolo, luogo e link consultando le parole chiave personalizzate."""
    full_text = f"{title} {location} {desc}".lower()
    custom_kw = config.get("custom_keywords", {})
    
    # 1. Voli, Treni, Bus, Navette, Aeroporto e Viaggi (Priorità Trasporti ✈️🚆🚌)
    travel_keywords = custom_kw.get("captain", [
        "flight", "volo", "airport", "aeroporto", "bus", "navetta", "shuttle", "pullman", 
        "ryanair", "easyjet", "wizz", "ita airways", "treno", "frecciarossa", "italo", 
        "stazione", "viaggio", "partenza", "gate", "terminal", "imbarco", "boarding", "taxi", "uber"
    ])
    if any(re.search(r'\b' + re.escape(k) + r'\b', full_text) if len(k) <= 4 else (k in full_text) for k in travel_keywords):
        maps_query = location if (location and location != "missing value") else title
        encoded_query = urllib.parse.quote(maps_query)
        return {
            "event_type": "travel",
            "pilot_type": "captain",
            "provider": "Volo / Viaggio / Bus ✈️🚌",
            "action_btn_text": "🗺️ INDICAZIONI MAPPE",
            "action_url": meeting_url if meeting_url else f"https://maps.apple.com/?q={encoded_query}",
            "theme_name": "Sky Blue",
            "is_travel": True
        }

    # 2. Cene, Pranzi, Ristoranti, Cibo, Aperitivi (Tema Chef 👨‍🍳🍕🍽️)
    food_keywords = custom_kw.get("chef", [
        "cena", "pranzo", "dinner", "lunch", "ristorante", "pizza", "pizzeria", "sushi", 
        "aperitivo", "apericena", "osteria", "trattoria", "cibo", "food", "mangiare", "pub", "burger"
    ])
    if any(k in full_text for k in food_keywords):
        maps_query = location if (location and location != "missing value") else f"Ristorante {title}"
        encoded_query = urllib.parse.quote(maps_query)
        return {
            "event_type": "food",
            "pilot_type": "chef",
            "provider": "Cena / Cibo 🍕🍽️",
            "action_btn_text": "🗺️ INDICAZIONI RISTORANTE",
            "action_url": meeting_url if meeting_url else f"https://maps.apple.com/?q={encoded_query}",
            "theme_name": "Coral Food",
            "is_travel": True
        }

    # 3. Riunioni Video Online
    if meeting_url:
        if "serenis.it" in meeting_url or "serenis" in full_text:
            return {
                "event_type": "health",
                "pilot_type": "zen_duck", # Papero Zen 🦆🌸
                "provider": "Serenis 🛋️",
                "action_btn_text": "🚀 PARTECIPA AL MEETING",
                "action_url": meeting_url,
                "theme_name": "Teal Zen",
                "is_travel": False
            }
        elif "meet.google.com" in meeting_url:
            return {
                "event_type": "video_meeting",
                "pilot_type": "duck",
                "provider": "Google Meet 🟢",
                "action_btn_text": "🚀 PARTECIPA ORA",
                "action_url": meeting_url,
                "theme_name": "Google Green",
                "is_travel": False
            }
        elif "zoom.us" in meeting_url:
            return {
                "event_type": "video_meeting",
                "pilot_type": "duck",
                "provider": "Zoom 🔷",
                "action_btn_text": "🚀 ENTRA IN ZOOM",
                "action_url": meeting_url,
                "theme_name": "Zoom Blue",
                "is_travel": False
            }
        elif "teams.microsoft.com" in meeting_url or "teams.live.com" in meeting_url:
            return {
                "event_type": "video_meeting",
                "pilot_type": "duck",
                "provider": "MS Teams 🟣",
                "action_btn_text": "🚀 PARTECIPA SU TEAMS",
                "action_url": meeting_url,
                "theme_name": "Teams Purple",
                "is_travel": False
            }
        else:
            return {
                "event_type": "video_meeting",
                "pilot_type": "duck",
                "provider": "Video Call 🌐",
                "action_btn_text": "🚀 PARTECIPA ORA",
                "action_url": meeting_url,
                "theme_name": "Classic Blue",
                "is_travel": False
            }

    # 4. Studio, Università, Lezioni, Esami, Corsi
    study_keywords = custom_kw.get("owl", [
        "universit", "uni", "esame", "esami", "lezione", "lezioni", 
        "politecnico", "tesi", "smartgrid", "building", "ict", 
        "satellite", "ricerca operativa", "corso", "aula"
    ])
    if any(re.search(r'\b' + re.escape(k) + r'\b', full_text) if len(k) <= 4 else (k in full_text) for k in study_keywords):
        maps_query = location if (location and location != "missing value") else "Politecnico Università"
        encoded_query = urllib.parse.quote(maps_query)
        return {
            "event_type": "study",
            "pilot_type": "owl", # Gufo Studioso 🦉🎓
            "provider": "Studio / Uni 🎓",
            "action_btn_text": "🗺️ INDICAZIONI AULA" if location and location != "missing value" else "📚 DETTAGLI STUDIO",
            "action_url": f"https://maps.apple.com/?q={encoded_query}" if location and location != "missing value" else "https://calendar.google.com",
            "theme_name": "Amber Academic",
            "is_travel": bool(location and location != "missing value")
        }

    # 5. Salute, Terapia, Relax, Yoga (Zen Duck 🦆🌸)
    zen_keywords = custom_kw.get("zen_duck", ["serenis", "terapia", "yoga", "meditazione", "benessere", "relax"])
    if any(k in full_text for k in zen_keywords):
        return {
            "event_type": "health",
            "pilot_type": "zen_duck",
            "provider": "Salute & Relax 🌿",
            "action_btn_text": "🗺️ APRI MAPPE" if location and location != "missing value" else "🌸 DETTAGLI",
            "action_url": f"https://maps.apple.com/?q={urllib.parse.quote(location)}" if location and location != "missing value" else "https://calendar.google.com",
            "theme_name": "Teal Zen",
            "is_travel": bool(location and location != "missing value")
        }

    # 6. Appuntamenti in Presenza / Luoghi da raggiungere con Tempo di Spostamento
    driver_keywords = custom_kw.get("driver", ["palestra", "dentista", "dottore", "visita", "medico", "allenamento", "studio", "ufficio"])
    if any(k in full_text for k in driver_keywords) or (location and location != "missing value" and len(location.strip()) > 2):
        dest = location if (location and location != "missing value") else title
        encoded_dest = urllib.parse.quote(dest)
        return {
            "event_type": "in_person",
            "pilot_type": "driver", # Pilota Viaggiatore 🚗💨
            "provider": "In Presenza 📍 Tempo di Spostamento!",
            "action_btn_text": "🗺️ VAI CON MAPPE (NAVIGA)",
            "action_url": f"https://maps.apple.com/?daddr={encoded_dest}",
            "theme_name": "Emerald Travel",
            "is_travel": True
        }

    # 7. Evento Generico / Promemoria
    return {
        "event_type": "general",
        "pilot_type": "duck",
        "provider": "Promemoria ⏰",
        "action_btn_text": "📋 APRI EVENTO",
        "action_url": "https://calendar.google.com",
        "theme_name": "Sunset Orange",
        "is_travel": False
    }

def get_upcoming_meetings():
    """Scansiona i calendari del Mac e restituisce tutti gli eventi e riunioni con classificazione tematica e filtri dinamici."""
    ignored = config.get("ignored_calendars", [
        "Festività in Italia", "Birthdays", "Scheduled Reminders", "Siri Suggestions"
    ])
    
    # Costruisci condizioni di esclusione AppleScript
    if ignored:
        cond_parts = [f'cName is not "{cal}"' for cal in ignored]
        cal_filter_cond = " and ".join(cond_parts)
    else:
        cal_filter_cond = "true"

    script = f'''
    tell application "Calendar"
        set todayStart to (current date) - (2 * hours)
        set todayEnd to (current date) + (24 * hours)
        set outEvents to {{}}
        repeat with cal in calendars
            set cName to name of cal
            if {cal_filter_cond} then
                try
                    set evs to (every event of cal whose start date >= todayStart and start date <= todayEnd)
                    repeat with ev in evs
                        set t to summary of ev
                        set s to (start date of ev) as string
                        set e to (end date of ev) as string
                        set u to ""
                        try
                            set u to url of ev
                        end try
                        set l to ""
                        try
                            set l to location of ev
                        end try
                        set d to ""
                        try
                            set d to description of ev
                        end try
                        set end of outEvents to (t & "<|>" & s & "<|>" & e & "<|>" & u & "<|>" & l & "<|>" & d)
                    end repeat
                end try
            end if
        end repeat
        set AppleScript's text item delimiters to "
###EVENT###
"
        return outEvents as string
    end tell
    '''
    
    try:
        res = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=60)
        if res.returncode != 0 or not res.stdout.strip():
            return []
            
        raw_events = res.stdout.strip().split('###EVENT###')
        meetings = []
        
        for raw_ev in raw_events:
            parts = raw_ev.strip().split('<|>')
            if len(parts) < 6:
                continue
                
            title, start_str, end_str, url_raw, loc_raw, desc_raw = parts[:6]
            
            meeting_url = (
                extract_meeting_url(url_raw) or 
                extract_meeting_url(loc_raw) or 
                extract_meeting_url(desc_raw)
            )
            
            start_dt = parse_applescript_date(start_str)
            end_dt = parse_applescript_date(end_str)
            
            if not start_dt:
                continue

            loc_clean = loc_raw if loc_raw != "missing value" else ""
            desc_clean = desc_raw if desc_raw != "missing value" else ""
            
            meta = classify_event(title, loc_clean, desc_clean, meeting_url)
            
            meetings.append({
                "title": title,
                "start_time": start_dt,
                "end_time": end_dt,
                "meeting_url": meeting_url,
                "location": loc_clean,
                "description": desc_clean,
                "event_type": meta["event_type"],
                "pilot_type": meta["pilot_type"],
                "provider": meta["provider"],
                "action_btn_text": meta["action_btn_text"],
                "action_url": meta["action_url"],
                "theme_name": meta["theme_name"],
                "is_travel": meta["is_travel"]
            })
            
        meetings.sort(key=lambda x: x["start_time"])
        return meetings

    except Exception as e:
        print(f"Errore scansione calendario: {e}")
        return []

if __name__ == "__main__":
    print("Testing Smart Event Classifier with Food & Travel...")
    results = get_upcoming_meetings()
    print(f"Trovati {len(results)} eventi nelle prossime 24h:")
    for m in results:
        print(f"- [{m['provider']}] {m['title']} alle {m['start_time'].strftime('%H:%M')} (Pilota: {m['pilot_type']}) -> Azione: {m['action_btn_text']}")
