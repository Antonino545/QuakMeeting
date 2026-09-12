"""
Multi-Modal Travel Time Estimation & Apple Maps Routing Service for FlightDeck.
Calculates ETA for Public Transit (Bus, Metro, Tram, Treno), Driving, Walking, and Cycling.
"""
import os
import json
import time
import urllib.parse
import urllib.request
import logging
import threading
import math
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple

from core.services.config_service import config_service, ConfigService

logger = logging.getLogger("FlightDeck.ETAService")

ETA_CACHE_FILE = os.path.expanduser("~/.flightdeck/eta_cache.json")

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

def validate_address(address: str, city_context: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Validates departure/destination address format via AddressService.
    Returns (is_valid, error_code).
    Empty address is considered valid (clears departure address).
    """
    from core.services.address_service import address_service
    is_valid, _cand, err = address_service.verify_address(address, city_context=city_context)
    return is_valid, err


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
        self._init_mapkit()
        self._initialized = True

    def _init_mapkit(self) -> None:
        """Initializes MapKit metadata on macOS for native Apple Maps ETA retrieval."""
        import sys
        if sys.platform != "darwin":
            return
        try:
            import objc
            try:
                objc.loadBundle('CoreLocation', globals(), bundle_path='/System/Library/Frameworks/CoreLocation.framework')
                objc.loadBundle('MapKit', globals(), bundle_path='/System/Library/Frameworks/MapKit.framework')
            except Exception as e:
                logger.debug(f"Bundle load notice: {e}")
            objc.registerMetaDataForSelector(
                b'MKDirections',
                b'calculateETAWithCompletionHandler:',
                {
                    'arguments': {
                        2: {
                            'callable': {
                                'retval': {'type': b'v'},
                                'arguments': {
                                    0: {'type': b'^v'},
                                    1: {'type': b'@'},
                                    2: {'type': b'@'}
                                }
                            }
                        }
                    }
                }
            )
            self.MKDirections = objc.lookUpClass('MKDirections')
            self.MKDirectionsRequest = objc.lookUpClass('MKDirectionsRequest')
            self.MKMapItem = objc.lookUpClass('MKMapItem')
            self.MKPlacemark = objc.lookUpClass('MKPlacemark')
            self._mapkit_ready = True
        except Exception as e:
            logger.debug(f"MapKit initialization notice: {e}")

    def _calculate_apple_maps_eta(self, coords_orig: Tuple[float, float], coords_dest: Tuple[float, float], mode: str) -> Optional[Tuple[int, float]]:
        """Calculates live ETA and distance directly from Apple Maps via MapKit on macOS."""
        import sys
        if sys.platform != "darwin":
            return None

        if not getattr(self, "_mapkit_ready", False):
            self._init_mapkit()

        if not (getattr(self, "MKDirections", None) and getattr(self, "MKDirectionsRequest", None) and getattr(self, "MKMapItem", None) and getattr(self, "MKPlacemark", None)):
            return None

        try:
            import Foundation

            lat1, lon1 = coords_orig
            lat2, lon2 = coords_dest

            pm1 = self.MKPlacemark.alloc().initWithCoordinate_addressDictionary_((lat1, lon1), None)
            pm2 = self.MKPlacemark.alloc().initWithCoordinate_addressDictionary_((lat2, lon2), None)

            item1 = self.MKMapItem.alloc().initWithPlacemark_(pm1)
            item2 = self.MKMapItem.alloc().initWithPlacemark_(pm2)

            req = self.MKDirectionsRequest.alloc().init()
            req.setSource_(item1)
            req.setDestination_(item2)

            # Transport types: Automobile=1, Walking=2, Transit=4
            t_type = 4
            if mode == "automobile":
                t_type = 1
            elif mode in ("walking", "bicycling"):
                t_type = 2

            req.setTransportType_(t_type)

            directions = self.MKDirections.alloc().initWithRequest_(req)
            sem = threading.Semaphore(0)
            res: Dict[str, Any] = {}

            def completion(response, error):
                if not error and response:
                    sec = response.expectedTravelTime()
                    dist = response.distance()
                    if sec and sec > 0:
                        res["minutes"] = max(2, round(sec / 60.0))
                        res["km"] = round(dist / 1000.0, 1)
                sem.release()

            directions.calculateETAWithCompletionHandler_(completion)

            start = time.time()
            while not sem.acquire(blocking=False):
                Foundation.NSRunLoop.currentRunLoop().runMode_beforeDate_(
                    Foundation.NSDefaultRunLoopMode,
                    Foundation.NSDate.dateWithTimeIntervalSinceNow_(0.05)
                )
                if time.time() - start > 4.0:
                    break

            if "minutes" in res and "km" in res:
                return res["minutes"], res["km"]

        except Exception as e:
            logger.debug(f"Apple Maps ETA query failed: {e}")

        return None

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

    def clear_cache(self) -> None:
        """Clears memory and disk ETA caches."""
        self._memory_cache = {}
        try:
            if os.path.exists(ETA_CACHE_FILE):
                os.remove(ETA_CACHE_FILE)
        except Exception as e:
            logger.debug(f"Could not remove ETA cache file: {e}")

    def build_maps_url(self, origin: Optional[str], destination: str, mode: str = "transit") -> str:
        """Builds a routing map deep link (Apple Maps on macOS, Google Maps otherwise)."""
        import sys
        home_city = (self.config.get("home_city", "") or "").strip() if self.config else ""
        
        dest_query = destination
        if home_city and destination and home_city.lower() not in destination.lower() and "," not in destination:
            dest_query = f"{destination}, {home_city}"

        orig_query = origin
        if origin and home_city and home_city.lower() not in origin.lower() and "," not in origin:
            orig_query = f"{origin}, {home_city}"

        if sys.platform == "darwin":
            return self._build_apple_maps_url(orig_query, dest_query, mode)
        else:
            return self._build_google_maps_url(orig_query, dest_query, mode)

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

    def _geocode_address(
        self,
        address: str,
        default_city: Optional[str] = None,
        proximity_coords: Optional[Tuple[float, float]] = None
    ) -> Optional[Tuple[float, float]]:
        """Geocodes an address string to (latitude, longitude) coordinates using central AddressService."""
        cleaned_addr = (address or "").strip()
        if not cleaned_addr:
            return None

        from core.services.address_service import address_service
        is_valid, cand, _ = address_service.verify_address(
            cleaned_addr,
            city_context=default_city,
            proximity_coords=proximity_coords
        )
        if is_valid and cand and (cand.lat != 0.0 or cand.lon != 0.0):
            return cand.lat, cand.lon
        return None

    def _query_opensource_route(self, coords_orig: Tuple[float, float], coords_dest: Tuple[float, float], mode: str) -> Optional[Tuple[int, float]]:
        """Queries open-source OpenStreetMap / OSRM routing network with profile-specific endpoints."""
        lat1, lon1 = coords_orig
        lat2, lon2 = coords_dest

        # Map to OpenStreetMap Deutschland routing profiles
        profile = "routed-car"
        if mode == "walking":
            profile = "routed-foot"
        elif mode == "bicycling":
            profile = "routed-bike"

        candidate_urls = [
            f"https://routing.openstreetmap.de/{profile}/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false",
            f"https://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"
        ]

        headers = {"User-Agent": "FlightDeck/1.0 (https://github.com/Antonino545/FlightDeck)"}

        for url in candidate_urls:
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=4) as resp:
                    route_data = json.loads(resp.read().decode("utf-8"))
                    if route_data.get("routes") and len(route_data["routes"]) > 0:
                        raw_sec = route_data["routes"][0]["duration"]
                        dist_m = route_data["routes"][0]["distance"]
                        distance_km = round(dist_m / 1000.0, 1)

                        if mode == "automobile":
                            # Urban driving traffic multiplier + parking/traffic lights
                            duration_minutes = max(5, round((raw_sec / 60.0) * 1.35 + 4))
                        elif mode == "transit":
                            # Real-world public transit factor: bus/tram headways + station walks + stops
                            duration_minutes = max(15, round((raw_sec / 60.0) * 1.8 + 12))
                        elif mode == "walking":
                            if "routed-foot" in url:
                                duration_minutes = max(2, round(raw_sec / 60.0))
                            else:
                                duration_minutes = max(2, round((distance_km / 5.0) * 60.0))
                        elif mode == "bicycling":
                            if "routed-bike" in url:
                                duration_minutes = max(2, round(raw_sec / 60.0 + 2))
                            else:
                                duration_minutes = max(2, round((distance_km / 15.0) * 60.0 + 2))
                        else:
                            duration_minutes = max(5, round(raw_sec / 60.0))

                        return duration_minutes, distance_km
            except Exception as e:
                logger.debug(f"Open-source routing query error for {url}: {e}")

        return None

    def calculate_eta(
        self,
        origin: str,
        destination: str,
        mode: Optional[str] = None,
        allow_auto_mode: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Calculates travel duration (minutes) and distance (km) for the specified mode.
        Auto-suggests walking route if destination is within walking distance (< threshold_km).
        Returns dict with minutes, km, mode, and ready-to-use Maps URL.
        """
        if not origin or not destination or origin.strip() == "" or destination.strip() == "":
            logger.debug("ETA skipped because origin or destination is empty.")
            return None

        selected_mode = mode or self.config.get("transport_mode", "transit")
        home_city = (self.config.get("home_city", "") or "").strip() if self.config else ""
        if home_city:
            cache_key = f"route_{origin.lower().strip()}_{destination.lower().strip()}_{selected_mode}_{home_city.lower()}"
        else:
            cache_key = f"route_{origin.lower().strip()}_{destination.lower().strip()}_{selected_mode}"

        if cache_key in self._memory_cache:
            logger.debug("ETA memory cache hit: mode=%s origin=%r destination=%r.", selected_mode, origin, destination)
            return self._memory_cache[cache_key]

        logger.debug("Calculating ETA: mode=%s origin=%r destination=%r.", selected_mode, origin, destination)

        coords_orig = self._geocode_address(origin, default_city=home_city)
        coords_dest = self._geocode_address(destination, default_city=home_city, proximity_coords=coords_orig)

        duration_minutes = 30
        distance_km = 8.0
        auto_walking = False

        if coords_orig and coords_dest:
            lat1, lon1 = coords_orig
            lat2, lon2 = coords_dest

            # Straight-line distance estimate (Haversine)
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            est_distance_km = round(6371.0 * c, 2)

            auto_threshold = float(self.config.get("auto_walking_threshold_km", 1.2)) if self.config else 1.2
            if (
                allow_auto_mode
                and auto_threshold > 0
                and selected_mode in ("transit", "automobile")
                and est_distance_km <= auto_threshold
            ):
                selected_mode = "walking"
                auto_walking = True
                logger.debug("Automatically switching ETA mode to walking for %.2f km route.", est_distance_km)

            # 1. On macOS: Native Apple Maps live ETA via MapKit
            apple_eta = self._calculate_apple_maps_eta(coords_orig, coords_dest, selected_mode)
            if apple_eta:
                duration_minutes, distance_km = apple_eta
            else:
                # 2. On Linux / Ubuntu (or macOS fallback): Open-source OpenStreetMap / OSRM multi-modal router
                os_eta = self._query_opensource_route(coords_orig, coords_dest, selected_mode)
                if os_eta:
                    duration_minutes, distance_km = os_eta
                else:
                    # 3. Offline geometry fallback: Haversine distance
                    distance_km = round(est_distance_km * 1.35, 1)

                    if selected_mode == "automobile":
                        duration_minutes = max(5, round((distance_km / 25.0) * 60.0 + 4))
                    elif selected_mode == "transit":
                        duration_minutes = max(15, round((distance_km / 12.0) * 60.0 + 10))
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
            "auto_walking": auto_walking,
            "mode_icon": mode_icon,
            "mode_label": mode_label,
            "maps_url": maps_url,
            "origin": origin,
            "destination": destination
        }

        self._memory_cache[cache_key] = result
        self._save_cache()
        logger.debug("ETA calculated: %d minutes, %.1f km, mode=%s.", duration_minutes, distance_km, selected_mode)
        return result

    def get_departure_time(self, start_time: datetime, travel_minutes: int, buffer_minutes: Optional[int] = None) -> datetime:
        """Calculates recommended departure time from home given start time and travel duration."""
        buf = buffer_minutes if buffer_minutes is not None else int(self.config.get("eta_buffer_minutes", 10))
        total_lead = travel_minutes + buf
        logger.debug("Departure time calculated: travel=%d buffer=%d total=%d minutes.", travel_minutes, buf, total_lead)
        return start_time - timedelta(minutes=total_lead)

# Global singleton instance
eta_service = ETAService()
