import json
import logging
import time
import urllib.request
from math import asin, cos, radians, sin, sqrt

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.neighborhood import Neighborhood
from app.schemas.location import (
    LocationSearchResultItem,
    NearbyNeighborhoodResponse,
    NeighborhoodMarkerResponse,
    NeighborhoodMarkerWithScoreResponse,
    NearestNeighborhoodItem,
    NearestNeighborhoodResponse,
)
from app.services.myki_service import calculate_myki_from_environmental_data
from app.services.statistics_service import get_latest_environmental_record

_logger = logging.getLogger(__name__)

_geocode_cache: dict[str, str | None] = {}
_geocode_cache_ts: dict[str, float] = {}
_GEOCODE_TTL = 300


def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    earth_radius_km = 6371.0

    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)

    delta_lat = lat2_rad - lat1_rad
    delta_lon = lon2_rad - lon1_rad

    a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return round(earth_radius_km * c, 2)


def get_all_neighborhoods(db: Session) -> list[Neighborhood]:
    return list(db.scalars(select(Neighborhood)).all())


def find_nearest_neighborhood(
    db: Session, latitude: float, longitude: float
) -> NearestNeighborhoodResponse | None:
    neighborhoods = get_all_neighborhoods(db)
    if not neighborhoods:
        return None

    nearest = min(
        neighborhoods,
        key=lambda neighborhood: calculate_distance_km(
            latitude, longitude, neighborhood.latitude, neighborhood.longitude
        ),
    )
    distance_km = calculate_distance_km(latitude, longitude, nearest.latitude, nearest.longitude)

    return NearestNeighborhoodResponse(
        neighborhood=NearestNeighborhoodItem(
            id=nearest.id,
            name=nearest.name,
            city=nearest.city,
            district=nearest.district,
            latitude=nearest.latitude,
            longitude=nearest.longitude,
        ),
        distance_km=distance_km,
    )


def find_nearby_neighborhoods(
    db: Session, latitude: float, longitude: float, radius_km: float, limit: int
) -> list[NearbyNeighborhoodResponse]:
    neighborhoods = get_all_neighborhoods(db)

    items: list[NearbyNeighborhoodResponse] = []
    for neighborhood in neighborhoods:
        distance_km = calculate_distance_km(
            latitude, longitude, neighborhood.latitude, neighborhood.longitude
        )
        if distance_km <= radius_km:
            items.append(
                NearbyNeighborhoodResponse(
                    id=neighborhood.id,
                    name=neighborhood.name,
                    city=neighborhood.city,
                    district=neighborhood.district,
                    latitude=neighborhood.latitude,
                    longitude=neighborhood.longitude,
                    distance_km=distance_km,
                )
            )

    items.sort(key=lambda item: item.distance_km)
    return items[:limit]


def get_neighborhood_markers(db: Session) -> list[NeighborhoodMarkerResponse]:
    neighborhoods = get_all_neighborhoods(db)
    return [
        NeighborhoodMarkerResponse(
            id=neighborhood.id,
            name=neighborhood.name,
            city=neighborhood.city,
            district=neighborhood.district,
            latitude=neighborhood.latitude,
            longitude=neighborhood.longitude,
        )
        for neighborhood in neighborhoods
    ]


def reverse_geocode_neighborhood_name(lat: float, lon: float) -> str | None:
    cache_key = f"{lat:.5f},{lon:.5f}"
    now = time.time()
    if cache_key in _geocode_cache and (now - _geocode_cache_ts.get(cache_key, 0)) < _GEOCODE_TTL:
        return _geocode_cache[cache_key]

    url = (
        f"https://nominatim.openstreetmap.org/reverse"
        f"?format=json&lat={lat}&lon={lon}&zoom=16&accept-language=tr"
    )
    try:
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "runway-backend/1.0",
            },
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())

        address = data.get("address", {})
        name = (
            address.get("neighbourhood")
            or address.get("suburb")
            or address.get("quarter")
            or address.get("town_district")
        )
        if name:
            for suffix in (" Mahallesi", " mahallesi", " Mah."):
                name = name.removesuffix(suffix)

        _geocode_cache[cache_key] = name
        _geocode_cache_ts[cache_key] = now
        return name

    except Exception as exc:
        _logger.warning("Nominatim reverse geocode başarısız: %s", exc)
        _geocode_cache[cache_key] = None
        _geocode_cache_ts[cache_key] = now
        return None


_search_cache: dict[str, tuple[list[LocationSearchResultItem], float]] = {}
_SEARCH_TTL = 120  # 2 dakika


def _nominatim_search(q: str, limit: int = 5) -> list[LocationSearchResultItem]:
    url = (
        f"https://nominatim.openstreetmap.org/search"
        f"?q={urllib.request.quote(q + ' Isparta')}&format=json"
        f"&limit={limit}&accept-language=tr&countrycodes=tr&addressdetails=1"
    )
    try:
        req = urllib.request.Request(
            url,
            headers={"Accept": "application/json", "User-Agent": "runway-backend/1.0"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            results = json.loads(resp.read().decode())
    except Exception as exc:
        _logger.warning("Nominatim search başarısız q=%r: %s", q, exc)
        return []

    # Isparta Merkez ilçesi için kaba koordinat kutusu
    _LAT_MIN, _LAT_MAX = 37.65, 37.95
    _LON_MIN, _LON_MAX = 30.40, 30.70

    items: list[LocationSearchResultItem] = []
    for r in results:
        addr = r.get("address", {})
        try:
            lat, lon = float(r["lat"]), float(r["lon"])
        except (KeyError, ValueError):
            continue
        if not (_LAT_MIN <= lat <= _LAT_MAX and _LON_MIN <= lon <= _LON_MAX):
            continue
        raw_name = (
            addr.get("neighbourhood")
            or addr.get("suburb")
            or addr.get("quarter")
            or addr.get("village")
            or addr.get("town")
            or r.get("display_name", "").split(",")[0].strip()
        )
        for _sfx in (" Mahallesi", " mahallesi", " Mah."):
            raw_name = raw_name.removesuffix(_sfx)
        name = raw_name
        city = addr.get("province") or addr.get("state") or "Isparta"
        district = addr.get("city") or addr.get("county") or ""
        if district.endswith(" Merkez"):
            district = district[: -len(" Merkez")]
        items.append(
            LocationSearchResultItem(
                name=name,
                display_name=r.get("display_name", name),
                city=city,
                district=district,
                latitude=float(r["lat"]),
                longitude=float(r["lon"]),
                neighborhood_id=None,
                source="geocoding",
            )
        )
    return items


def search_locations(db: Session, q: str) -> list[LocationSearchResultItem]:
    q = q.strip()
    if not q:
        return []

    cache_key = q.lower()
    now = time.time()
    if cache_key in _search_cache:
        cached, ts = _search_cache[cache_key]
        if now - ts < _SEARCH_TTL:
            return cached

    # 1) DB araması (case-insensitive contains)
    db_rows = list(
        db.scalars(
            select(Neighborhood).where(Neighborhood.name.ilike(f"%{q}%"))
        ).all()
    )
    db_results: list[LocationSearchResultItem] = [
        LocationSearchResultItem(
            name=n.name,
            display_name=f"{n.name}, {n.district}, {n.city}",
            city=n.city,
            district=n.district,
            latitude=n.latitude,
            longitude=n.longitude,
            neighborhood_id=n.id,
            source="database",
        )
        for n in db_rows
    ]

    # 2) DB sonucu yetersizse Nominatim ile tamamla
    geocoding_results: list[LocationSearchResultItem] = []
    if len(db_results) < 3:
        raw = _nominatim_search(q)
        # DB'de zaten olan isimleri tekrar ekleme
        existing_names = {r.name.lower() for r in db_results}
        geocoding_results = [r for r in raw if r.name.lower() not in existing_names]

    merged = db_results + geocoding_results
    _search_cache[cache_key] = (merged, now)
    return merged


def get_neighborhood_markers_with_scores(db: Session) -> list[NeighborhoodMarkerWithScoreResponse]:
    neighborhoods = get_all_neighborhoods(db)
    items: list[NeighborhoodMarkerWithScoreResponse] = []

    for neighborhood in neighborhoods:
        latest_record = get_latest_environmental_record(db, neighborhood.id)
        myki_score = None
        myki_category = None

        if latest_record:
            myki_score, myki_category = calculate_myki_from_environmental_data(latest_record)

        items.append(
            NeighborhoodMarkerWithScoreResponse(
                id=neighborhood.id,
                name=neighborhood.name,
                city=neighborhood.city,
                district=neighborhood.district,
                latitude=neighborhood.latitude,
                longitude=neighborhood.longitude,
                myki_score=myki_score,
                myki_category=myki_category,
            )
        )

    return items
