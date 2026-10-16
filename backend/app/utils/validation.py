import re

ICAO24_RE = re.compile(r"^[0-9a-f]{6}$")
CALLSIGN_RE = re.compile(r"^[A-Z0-9]{2,8}$")


def clean_icao24(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.strip().lower()
    return cleaned if ICAO24_RE.match(cleaned) else None


def normalize_callsign(value: str | None) -> str | None:
    """opensky pads callsigns with spaces and sometimes drops the case"""
    if not value:
        return None
    cleaned = value.strip().upper()
    return cleaned or None


def normalize_code(value: str | None) -> str | None:
    """airport / airline style codes, upper-cased and trimmed"""
    if not value:
        return None
    cleaned = value.strip().upper()
    return cleaned or None
