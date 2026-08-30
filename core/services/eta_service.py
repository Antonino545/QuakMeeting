"""
Multi-Modal Travel Time Estimation & Apple Maps Routing Service for QuakMeeting.
Calculates ETA for Public Transit (Bus, Metro, Tram, Treno), Driving, Walking, and Cycling.
"""
import os
import json
import urllib.parse
import urllib.request
import logging
import threading
import math
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple

from core.services.config_service import config_service, ConfigService

logger = logging.getLogger("QuakMeeting.ETAService")

ETA_CACHE_FILE = os.path.expanduser("~/.quakmeeting/eta_cache.json")

MODE_ICONS = {
    "transit": "🚆",
    "automobile": "🚗",
    "walking": "🚶",
    "bicycling": "🚲"
}

MODE_LABELS = {
    "transit": "Public Transit",
    "automobile": "Driving",
    "walking": "Walking",
    "bicycling": "Cycling"
}

# Apple Maps Direction Flags
APPLE_MAPS_FLAGS = {
    "transit": "r",      # Public Transit (Bus / Metro / Train)
    "automobile": "d",   # Driving
    "walking": "w",      # Walking
    "bicycling": "b"     # Biking
}

def validate_address(address: str) -> Tuple[bool, Optional[str]]:
    """
    Validates departure/destination address format.
    Returns (is_valid, error_code).
    Expected format: Street / Via + House Number + City (e.g. 'Via Roma 10, Torino' or 'Corso Duca 24, 10129 Torino, Italy').
    Empty address is considered valid (clears departure address).
    """
    if not address or not address.strip():
        return True, None

    clean = address.strip()
    if len(clean) < 6:
        return False, "too_short"

    tokens = clean.replace(",", " ").replace(".", " ").split()
    if len(tokens) < 2:
        return False, "missing_city_or_street"

    # Must have at least one alphabetic word (street/city) of len >= 2
    alpha_tokens = [t for t in tokens if any(c.isalpha() for c in t) and len(t) >= 2]
    if len(alpha_tokens) < 2:
        return False, "missing_details"

    # Check if there is at least a digit (house number or CAP) or at least 3 descriptive words (e.g. "Piazza Castello Torino")
    has_digit = any(c.isdigit() for c in clean)
    if not has_digit and len(alpha_tokens) < 3:
        return False, "missing_number_or_cap"

    return True, None

class ETAService:
    """Calculates multi-modal route durations and builds Apple Maps navigation links."""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ETAService, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, config: Optional[ConfigService] = None):
        if self._initialized:
            return
        self.config = config or config_service
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._load_cache()
        self._initialized = True

    def _load_cache(self) -> None:
        if os.path.exists(ETA_CACHE_FILE):
            try:
                with open(ETA_CACHE_FILE, "r", encoding="utf-8") as f:
                    self._memory_cache = json.load(f)
            except Exception as e:
                logger.warning(f"Error loading ETA cache: {e}")

    def _save_cache(self) -> None:
        try:
            os.makedirs(os.path.dirname(ETA_CACHE_FILE), exist_ok=True)
            with open(ETA_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self._memory_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Error saving ETA cache: {e}")

    def build_maps_url(self, origin: Optional[str], destination: str, mode: str = "transit") -> str:
        """Builds a routing map deep link (Apple Maps on macOS, Google Maps otherwise)."""
        import sys
        if sys.platform == "darwin":
            return self._build_apple_maps_url(origin, destination, mode)
        else:
            return self._build_google_maps_url(origin, destination, mode)

    def _build_apple_maps_url(self, origin: Optional[str], destination: str, mode: str) -> str:
        encoded_dest = urllib.parse.quote(destination or "")
        dir_flag = APPLE_MAPS_FLAGS.get(mode, "r")

        if origin and origin.strip():
            encoded_orig = urllib.parse.quote(origin.strip())
            return f"https://maps.apple.com/?saddr={encoded_orig}&daddr={encoded_dest}&dirflg={dir_flag}"
        else:
            return f"https://maps.apple.com/?daddr={encoded_dest}&dirflg={dir_flag}"

    def _build_google_maps_url(self, origin: Optional[str], destination: str, mode: str) -> str:
        g_mode = "transit"
        if mode == "automobile": g_mode = "driving"
        elif mode == "walking": g_mode = "walking"
        elif mode == "bicycling": g_mode = "bicycling"

        encoded_dest = urllib.parse.quote(destination or "")
        if origin and origin.strip():
            encoded_orig = urllib.parse.quote(origin.strip())
            return f"https://www.google.com/maps/dir/?api=1&origin={encoded_orig}&destination={encoded_dest}&travelmode={g_mode}"
        else:
            return f"https://www.google.com/maps/dir/?api=1&destination={encoded_dest}&travelmode={g_mode}"

    def _geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """Geocodes an address string to (latitude, longitude) coordinates."""
        cache_key = f"geo_{address.lower().strip()}"
        if cache_key in self._memory_cache:
            coords = self._memory_cache[cache_key]
            return coords["lat"], coords["lon"]

        try:
            url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(address)}&format=json&limit=1"
            headers = {"User-Agent": "QuakMeeting-macOS/1.0"}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data and len(data) > 0:
                    lat = float(data[0]["lat"])
                    lon = float(data[0]["lon"])
                    self._memory_cache[cache_key] = {"lat": lat, "lon": lon}
                    self._save_cache()
                    return lat, lon
        except Exception as e:
            logger.debug(f"Geocoding error for '{address}': {e}")
        return None

    def calculate_eta(self, origin: str, destination: str, mode: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Calculates travel duration (minutes) and distance (km) for the specified mode.
        Returns dict with minutes, km, mode, and ready-to-use Apple Maps URL.
        """
        if not origin or not destination or origin.strip() == "" or destination.strip() == "":
            return None

        selected_mode = mode or self.config.get("transport_mode", "transit")
        cache_key = f"route_{origin.lower().strip()}_{destination.lower().strip()}_{selected_mode}"

        if cache_key in self._memory_cache:
            return self._memory_cache[cache_key]

        coords_orig = self._geocode_address(origin)
        coords_dest = self._geocode_address(destination)

        duration_minutes = 25
        distance_km = 8.0

        if coords_orig and coords_dest:
            lat1, lon1 = coords_orig
            lat2, lon2 = coords_dest

            try:
                # OSRM Driving base query
                osrm_url = f"https://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"
                headers = {"User-Agent": "QuakMeeting-macOS/1.0"}
                req = urllib.request.Request(osrm_url, headers=headers)
                with urllib.request.urlopen(req, timeout=4) as resp:
                    route_data = json.loads(resp.read().decode("utf-8"))
                    if route_data.get("routes") and len(route_data["routes"]) > 0:
                        drive_sec = route_data["routes"][0]["duration"]
                        dist_m = route_data["routes"][0]["distance"]
                        distance_km = round(dist_m / 1000.0, 1)

                        if selected_mode == "automobile":
                            duration_minutes = max(3, round(drive_sec / 60.0))
                        elif selected_mode == "transit":
                            # Transit factor (~1.4x driving time to account for bus stops & walking)
                            duration_minutes = max(5, round((drive_sec / 60.0) * 1.35 + 4))
                        elif selected_mode == "walking":
                            # 5 km/h walking speed
                            duration_minutes = max(2, round((distance_km / 5.0) * 60.0))
                        elif selected_mode == "bicycling":
                            # 15 km/h cycling speed
                            duration_minutes = max(2, round((distance_km / 15.0) * 60.0))
            except Exception as e:
                logger.debug(f"OSRM routing query error: {e}")
                # Approximate distance calculation via Haversine
                dlat = math.radians(lat2 - lat1)
                dlon = math.radians(lon2 - lon1)
                a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                distance_km = round(6371.0 * c * 1.3, 1) # 1.3 road curvature factor

                if selected_mode == "automobile":
                    duration_minutes = max(4, round((distance_km / 35.0) * 60.0))
                elif selected_mode == "transit":
                    duration_minutes = max(6, round((distance_km / 22.0) * 60.0 + 5))
                elif selected_mode == "walking":
                    duration_minutes = max(2, round((distance_km / 4.8) * 60.0))
                elif selected_mode == "bicycling":
                    duration_minutes = max(2, round((distance_km / 15.0) * 60.0))

        maps_url = self.build_maps_url(origin, destination, selected_mode)
        mode_icon = MODE_ICONS.get(selected_mode, "🚆")
        mode_label = MODE_LABELS.get(selected_mode, "Mezzi Pubblici")

        result = {
            "duration_minutes": duration_minutes,
            "distance_km": distance_km,
            "transport_mode": selected_mode,
            "mode_icon": mode_icon,
            "mode_label": mode_label,
            "maps_url": maps_url,
            "origin": origin,
            "destination": destination
        }

        self._memory_cache[cache_key] = result
        self._save_cache()
        return result

    def get_departure_time(self, start_time: datetime, travel_minutes: int, buffer_minutes: Optional[int] = None) -> datetime:
        """Calculates recommended departure time from home given start time and travel duration."""
        buf = buffer_minutes if buffer_minutes is not None else int(self.config.get("eta_buffer_minutes", 10))
        total_lead = travel_minutes + buf
        return start_time - timedelta(minutes=total_lead)

# Global singleton instance
eta_service = ETAService()
