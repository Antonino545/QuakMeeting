"""
Address Service for QuakMeeting.
Provides live address autocomplete suggestions, geocoding validation,
canonical address formatting, and multi-platform map deep links.
"""
import os
import json
import urllib.parse
import urllib.request
import logging
import sys
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Tuple, Dict, Any

logger = logging.getLogger("QuakMeeting.AddressService")

CACHE_DIR = os.path.expanduser("~/.quakmeeting")
ADDRESS_CACHE_FILE = os.path.join(CACHE_DIR, "address_cache.json")


@dataclass
class AddressCandidate:
    display_name: str
    short_address: str
    city: str
    postcode: str = ""
    state: str = ""
    country: str = ""
    lat: float = 0.0
    lon: float = 0.0
    raw: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @property
    def map_url(self) -> str:
        return AddressService.get_map_url(self.display_name, self.lat, self.lon)


class AddressService:
    """Manages address autocomplete searches, verification, and map previews."""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(AddressService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._suggestions_cache: Dict[str, List[AddressCandidate]] = {}
        self._verification_cache: Dict[str, Optional[AddressCandidate]] = {}
        self._load_cache()
        self._initialized = True

    def _load_cache(self) -> None:
        try:
            if os.path.exists(ADDRESS_CACHE_FILE):
                with open(ADDRESS_CACHE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for k, candidates in data.get("suggestions", {}).items():
                        self._suggestions_cache[k] = [AddressCandidate(**c) for c in candidates]
                    for k, candidate in data.get("verification", {}).items():
                        self._verification_cache[k] = AddressCandidate(**candidate) if candidate else None
        except Exception as e:
            logger.debug(f"Address cache load notice: {e}")

    def _save_cache(self) -> None:
        try:
            os.makedirs(CACHE_DIR, exist_ok=True)
            serializable = {
                "suggestions": {
                    k: [c.to_dict() for c in v]
                    for k, v in list(self._suggestions_cache.items())[-100:]
                },
                "verification": {
                    k: (v.to_dict() if v else None)
                    for k, v in list(self._verification_cache.items())[-100:]
                }
            }
            with open(ADDRESS_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(serializable, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.debug(f"Address cache save notice: {e}")

    def clear_cache(self):
        """Clears memory and disk address caches."""
        self._suggestions_cache.clear()
        self._verification_cache.clear()
        self._save_cache()

    def search_suggestions(
        self,
        query: str,
        city_context: Optional[str] = None,
        limit: int = 5
    ) -> List[AddressCandidate]:
        """
        Searches address autocomplete candidates with context bias.
        Queries Nominatim with fallback to Photon.
        """
        cleaned_query = (query or "").strip()
        if len(cleaned_query) < 3:
            return []

        city = (city_context or "").strip()
        cache_key = f"{cleaned_query.lower()}|{city.lower()}|{limit}"
        if cache_key in self._suggestions_cache:
            return self._suggestions_cache[cache_key]

        candidates = self._query_nominatim(cleaned_query, city, limit)
        if not candidates:
            candidates = self._query_photon(cleaned_query, city, limit)

        if candidates:
            self._suggestions_cache[cache_key] = candidates
            self._save_cache()

        return candidates

    def verify_address(
        self,
        address: str,
        city_context: Optional[str] = None
    ) -> Tuple[bool, Optional[AddressCandidate], Optional[str]]:
        """
        Validates an address against real-world map data.
        Returns (is_valid, matched_candidate, error_code).
        Empty address is valid (clearing address).
        """
        cleaned = (address or "").strip()
        if not cleaned:
            return True, None, None

        if len(cleaned) < 3:
            return False, None, "too_short"

        city = (city_context or "").strip()
        cache_key = f"verify_{cleaned.lower()}|{city.lower()}"
        if cache_key in self._verification_cache:
            cand = self._verification_cache[cache_key]
            if cand:
                return True, cand, None
            return False, None, "not_found"

        candidates = self.search_suggestions(cleaned, city_context=city, limit=1)
        if candidates:
            best = candidates[0]
            self._verification_cache[cache_key] = best
            self._save_cache()
            return True, best, None

        self._verification_cache[cache_key] = None
        self._save_cache()
        return False, None, "not_found"

    def _query_nominatim(self, query: str, city: str, limit: int) -> List[AddressCandidate]:
        """Queries OpenStreetMap Nominatim search API."""
        search_query = query
        if city and city.lower() not in query.lower() and "," not in query:
            search_query = f"{query}, {city}"

        encoded = urllib.parse.quote(search_query)
        url = f"https://nominatim.openstreetmap.org/search?q={encoded}&format=json&addressdetails=1&limit={limit}"
        headers = {"User-Agent": "QuakMeeting/1.0 (https://github.com/Antonino545/QuakMeeting)"}

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                candidates = []
                for item in data:
                    addr_info = item.get("address", {})
                    road = addr_info.get("road") or addr_info.get("pedestrian") or addr_info.get("street") or ""
                    house_num = addr_info.get("house_number", "")
                    place_city = (
                        addr_info.get("city")
                        or addr_info.get("town")
                        or addr_info.get("village")
                        or addr_info.get("municipality")
                        or ""
                    )
                    postcode = addr_info.get("postcode", "")
                    state = addr_info.get("state", "")
                    country = addr_info.get("country", "")

                    poi_name = item.get("name") or addr_info.get("amenity") or addr_info.get("university") or addr_info.get("college") or ""
                    road_part = f"{road} {house_num}".strip() if road else ""

                    if poi_name and road_part and poi_name.lower() != road.lower():
                        short_addr = f"{poi_name} ({road_part})"
                    elif poi_name:
                        short_addr = poi_name
                    elif road_part:
                        short_addr = road_part
                    else:
                        short_addr = item.get("display_name", "").split(",")[0]

                    # Build clean canonical display string
                    display_parts = []
                    if short_addr:
                        display_parts.append(short_addr)
                    if place_city and place_city not in short_addr:
                        display_parts.append(place_city)
                    if state and state not in display_parts and state != place_city:
                        display_parts.append(state)
                    if country and country not in display_parts:
                        display_parts.append(country)

                    display_name = ", ".join(display_parts) if display_parts else item.get("display_name", "")

                    candidate = AddressCandidate(
                        display_name=display_name,
                        short_address=short_addr,
                        city=place_city,
                        postcode=postcode,
                        state=state,
                        country=country,
                        lat=float(item.get("lat", 0.0)),
                        lon=float(item.get("lon", 0.0)),
                        raw=item
                    )
                    candidates.append(candidate)
                return candidates
        except Exception as e:
            logger.debug(f"Nominatim search notice for '{query}': {e}")
            return []

    def _query_photon(self, query: str, city: str, limit: int) -> List[AddressCandidate]:
        """Queries Photon (Komoot OSM) geocoder as an ultra-fast autocomplete fallback."""
        search_query = query
        if city and city.lower() not in query.lower() and "," not in query:
            search_query = f"{query} {city}"

        encoded = urllib.parse.quote(search_query)
        url = f"https://photon.komoot.io/api/?q={encoded}&limit={limit}"
        headers = {"User-Agent": "QuakMeeting/1.0"}

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                features = data.get("features", [])
                candidates = []
                for feat in features:
                    props = feat.get("properties", {})
                    coords = feat.get("geometry", {}).get("coordinates", [0.0, 0.0])
                    lon = float(coords[0])
                    lat = float(coords[1])

                    name = props.get("name", "")
                    street = props.get("street", "")
                    housenumber = props.get("housenumber", "")
                    place_city = props.get("city") or props.get("town") or props.get("locality") or ""
                    postcode = props.get("postcode", "")
                    state = props.get("state", "")
                    country = props.get("country", "")

                    street_part = f"{street} {housenumber}".strip() if street else ""
                    if name and street_part and name.lower() != street.lower():
                        short_addr = f"{name} ({street_part})"
                    elif name:
                        short_addr = name
                    elif street_part:
                        short_addr = street_part
                    else:
                        short_addr = place_city or search_query

                    display_parts = []
                    if short_addr:
                        display_parts.append(short_addr)
                    if place_city and place_city not in short_addr:
                        display_parts.append(place_city)
                    if state and state not in display_parts and state != place_city:
                        display_parts.append(state)
                    if country and country not in display_parts:
                        display_parts.append(country)

                    display_name = ", ".join(display_parts) if display_parts else short_addr

                    candidates.append(AddressCandidate(
                        display_name=display_name,
                        short_address=short_addr,
                        city=place_city,
                        postcode=postcode,
                        state=state,
                        country=country,
                        lat=lat,
                        lon=lon,
                        raw=props
                    ))
                return candidates
        except Exception as e:
            logger.debug(f"Photon search notice for '{query}': {e}")
            return []

    @staticmethod
    def get_map_url(address: str, lat: Optional[float] = None, lon: Optional[float] = None) -> str:
        """Returns deep link URL for Apple Maps (macOS) or OpenStreetMap (Linux/other)."""
        encoded_addr = urllib.parse.quote(address or "")
        if sys.platform == "darwin":
            if lat is not None and lon is not None and (lat != 0.0 or lon != 0.0):
                return f"http://maps.apple.com/?ll={lat:.6f},{lon:.6f}&q={encoded_addr}"
            return f"http://maps.apple.com/?q={encoded_addr}"
        else:
            if lat is not None and lon is not None and (lat != 0.0 or lon != 0.0):
                return f"https://www.openstreetmap.org/?mlat={lat:.6f}&mlon={lon:.6f}#map=17/{lat:.6f}/{lon:.6f}"
            return f"https://www.openstreetmap.org/search?query={encoded_addr}"


address_service = AddressService()
