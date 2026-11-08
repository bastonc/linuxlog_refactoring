"""Maidenhead (QTH) locator helpers and callsign-prefix fallback lookup."""

from __future__ import annotations

import math
from typing import Any, Tuple
import re

from prefix_locators import PREFIX_LOCATORS

EARTH_RADIUS_KM = 6371.0088

_LOCATOR_FIELD_LON = 20.0
_LOCATOR_FIELD_LAT = 10.0
_LOCATOR_SQUARE_LON = 2.0
_LOCATOR_SQUARE_LAT = 1.0
_LOCATOR_SUBSQUARE_LON = _LOCATOR_SQUARE_LON / 24.0
_LOCATOR_SUBSQUARE_LAT = _LOCATOR_SQUARE_LAT / 24.0
_LOCATOR_EXTENDED_LON = _LOCATOR_SUBSQUARE_LON / 10.0
_LOCATOR_EXTENDED_LAT = _LOCATOR_SUBSQUARE_LAT / 10.0

_CALL_CLEAN_RE = re.compile(r"[^A-Z0-9/]")


def normalize_locator(value: Any) -> str:
    """Return a clean 2/4/6/8 character Maidenhead locator, or ``""``."""
    text = str(value or "").strip().upper()
    text = re.sub(r"\s+", "", text)
    if len(text) < 2 or len(text) % 2:
        return ""
    if not ("A" <= text[0] <= "R" and "A" <= text[1] <= "R"):
        return ""
    if len(text) >= 4 and not text[2:4].isdigit():
        return ""
    if len(text) >= 6 and not all("A" <= char <= "X" for char in text[4:6]):
        return ""
    if len(text) >= 8 and not text[6:8].isdigit():
        return ""
    return text[:8]


def locator_to_latlon(locator: str) -> Tuple[float, float]:
    """Return the centre of a Maidenhead locator as ``(latitude, longitude)``."""
    loc = normalize_locator(locator)
    if not loc:
        raise ValueError(f"Invalid Maidenhead locator: {locator!r}")

    longitude = -180.0 + (ord(loc[0]) - ord("A")) * _LOCATOR_FIELD_LON
    latitude = -90.0 + (ord(loc[1]) - ord("A")) * _LOCATOR_FIELD_LAT
    size_lon = _LOCATOR_FIELD_LON
    size_lat = _LOCATOR_FIELD_LAT

    if len(loc) >= 4:
        longitude += int(loc[2]) * _LOCATOR_SQUARE_LON
        latitude += int(loc[3]) * _LOCATOR_SQUARE_LAT
        size_lon = _LOCATOR_SQUARE_LON
        size_lat = _LOCATOR_SQUARE_LAT

    if len(loc) >= 6:
        longitude += (ord(loc[4]) - ord("A")) * _LOCATOR_SUBSQUARE_LON
        latitude += (ord(loc[5]) - ord("A")) * _LOCATOR_SUBSQUARE_LAT
        size_lon = _LOCATOR_SUBSQUARE_LON
        size_lat = _LOCATOR_SUBSQUARE_LAT

    if len(loc) >= 8:
        longitude += int(loc[6]) * _LOCATOR_EXTENDED_LON
        latitude += int(loc[7]) * _LOCATOR_EXTENDED_LAT
        size_lon = _LOCATOR_EXTENDED_LON
        size_lat = _LOCATOR_EXTENDED_LAT

    return latitude + size_lat / 2.0, longitude + size_lon / 2.0


def latlon_to_locator(latitude: float, longitude: float, precision: int = 6) -> str:
    """Convert coordinates to a Maidenhead locator (4 or 6 characters)."""
    try:
        lat = float(latitude)
        lon = float(longitude)
    except (TypeError, ValueError):
        return ""

    precision = 6 if precision not in (4, 6, 8) else precision
    lat = max(-90.0, min(90.0, lat))
    lon = ((lon + 180.0) % 360.0) - 180.0

    field_lon = min(17, max(0, int((lon + 180.0) // _LOCATOR_FIELD_LON)))
    field_lat = min(17, max(0, int((lat + 90.0) // _LOCATOR_FIELD_LAT)))
    locator = chr(ord("A") + field_lon) + chr(ord("A") + field_lat)

    if precision >= 4:
        lon_remainder = (lon + 180.0) - field_lon * _LOCATOR_FIELD_LON
        lat_remainder = (lat + 90.0) - field_lat * _LOCATOR_FIELD_LAT
        locator += str(int(lon_remainder // _LOCATOR_SQUARE_LON))
        locator += str(int(lat_remainder // _LOCATOR_SQUARE_LAT))

    if precision >= 6:
        lon_remainder = (lon + 180.0) - field_lon * _LOCATOR_FIELD_LON \
            - int(locator[2]) * _LOCATOR_SQUARE_LON
        lat_remainder = (lat + 90.0) - field_lat * _LOCATOR_FIELD_LAT \
            - int(locator[3]) * _LOCATOR_SQUARE_LAT
        locator += chr(ord("A") + int(lon_remainder // _LOCATOR_SUBSQUARE_LON))
        locator += chr(ord("A") + int(lat_remainder // _LOCATOR_SUBSQUARE_LAT))

    if precision >= 8:
        lon_remainder = (lon + 180.0) - field_lon * _LOCATOR_FIELD_LON \
            - int(locator[2]) * _LOCATOR_SQUARE_LON \
            - (ord(locator[4]) - ord("A")) * _LOCATOR_SUBSQUARE_LON
        lat_remainder = (lat + 90.0) - field_lat * _LOCATOR_FIELD_LAT \
            - int(locator[3]) * _LOCATOR_SQUARE_LAT \
            - (ord(locator[5]) - ord("A")) * _LOCATOR_SUBSQUARE_LAT
        locator += str(int(lon_remainder // _LOCATOR_EXTENDED_LON))
        locator += str(int(lat_remainder // _LOCATOR_EXTENDED_LAT))

    return locator


def distance_km(latitude_a: float, longitude_a: float, latitude_b: float, longitude_b: float) -> float:
    """Great-circle distance between two points in kilometres."""
    lat_a = math.radians(float(latitude_a))
    lon_a = math.radians(float(longitude_a))
    lat_b = math.radians(float(latitude_b))
    lon_b = math.radians(float(longitude_b))
    delta_lat = lat_b - lat_a
    delta_lon = lon_b - lon_a
    value = (
        math.sin(delta_lat / 2.0) ** 2
        + math.cos(lat_a) * math.cos(lat_b) * math.sin(delta_lon / 2.0) ** 2
    )
    return 2.0 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(value)))


def bearing_deg(latitude_a: float, longitude_a: float, latitude_b: float, longitude_b: float) -> float:
    """Initial bearing from the first point to the second, in degrees."""
    lat_a = math.radians(float(latitude_a))
    lat_b = math.radians(float(latitude_b))
    delta_lon = math.radians(float(longitude_b) - float(longitude_a))
    y = math.sin(delta_lon) * math.cos(lat_b)
    x = math.cos(lat_a) * math.sin(lat_b) \
        - math.sin(lat_a) * math.cos(lat_b) * math.cos(delta_lon)
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


def great_circle_points(latitude_a: float, longitude_a: float, latitude_b: float, longitude_b: float, steps: int = 64) -> list:
    """Return interpolated points along the great circle between two points."""
    lat_a = math.radians(float(latitude_a))
    lon_a = math.radians(float(longitude_a))
    lat_b = math.radians(float(latitude_b))
    lon_b = math.radians(float(longitude_b))

    value = (
        math.sin((lat_b - lat_a) / 2.0) ** 2
        + math.cos(lat_a) * math.cos(lat_b) * math.sin((lon_b - lon_a) / 2.0) ** 2
    )
    angular_distance = 2.0 * math.asin(min(1.0, math.sqrt(value)))
    if angular_distance < 1e-9:
        return [(math.degrees(lat_a), math.degrees(lon_a))]

    points = []
    for step in range(steps + 1):
        fraction = step / steps
        factor_a = math.sin((1.0 - fraction) * angular_distance) / math.sin(angular_distance)
        factor_b = math.sin(fraction * angular_distance) / math.sin(angular_distance)
        x = factor_a * math.cos(lat_a) * math.cos(lon_a) \
            + factor_b * math.cos(lat_b) * math.cos(lon_b)
        y = factor_a * math.cos(lat_a) * math.sin(lon_a) \
            + factor_b * math.cos(lat_b) * math.sin(lon_b)
        z = factor_a * math.sin(lat_a) + factor_b * math.sin(lat_b)
        points.append((math.degrees(math.atan2(z, math.hypot(x, y))),
                       math.degrees(math.atan2(y, x))))
    return points


def _callsign_candidates(callsign: str) -> list:
    clean = _CALL_CLEAN_RE.sub("", str(callsign or "").upper())
    if not clean:
        return []
    parts = [part for part in clean.split("/") if part]
    candidates = []
    for value in parts + [clean]:
        if value and value not in candidates:
            candidates.append(value)
    return candidates


def locator_from_callsign(callsign: str) -> Tuple[str, str]:
    """Return ``(locator, matched_prefix)`` from the prefix fallback table."""
    for candidate in _callsign_candidates(callsign):
        max_length = min(len(candidate), 6)
        for size in range(max_length, 0, -1):
            prefix = candidate[:size]
            locator = PREFIX_LOCATORS.get(prefix)
            if locator:
                return locator, prefix
    return "", ""


def locator_source_from_callsign(callsign: str) -> str:
    """Convenience wrapper returning only the fallback locator."""
    return locator_from_callsign(callsign)[0]
