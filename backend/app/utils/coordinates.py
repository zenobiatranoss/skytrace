import math

EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """great-circle distance between two points, in kilometers"""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def initial_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """compass bearing from point 1 to point 2, degrees clockwise from north"""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlambda = math.radians(lon2 - lon1)

    x = math.sin(dlambda) * math.cos(p2)
    y = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dlambda)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def valid_lat_lon(lat: float | None, lon: float | None) -> bool:
    if lat is None or lon is None:
        return False
    return -90 <= lat <= 90 and -180 <= lon <= 180


def normalize_longitude(lon: float) -> float:
    """fold a longitude back into [-180, 180)"""
    return ((lon + 180) % 360) - 180


def build_bounding_box(
    lat: float, lon: float, radius_km: float
) -> tuple[float, float, float, float]:
    """rough lat/lon box around a point - good enough for a map viewport query"""
    dlat = radius_km / 111.0
    dlon = radius_km / (111.0 * max(math.cos(math.radians(lat)), 0.01))

    lamin = max(-90.0, lat - dlat)
    lamax = min(90.0, lat + dlat)
    lomin = normalize_longitude(lon - dlon)
    lomax = normalize_longitude(lon + dlon)
    return lamin, lomin, lamax, lomax
