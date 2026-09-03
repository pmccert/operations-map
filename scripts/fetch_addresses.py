#!/usr/bin/env python3
"""
fetch_addresses.py
==================
Query the OpenStreetMap Overpass API for house addresses within a geographic
boundary and write a JSON file that maps each address to its lat/lon pair.

Output format
-------------
{
  "1234 Nesthorn Drive": {"lat": 34.857, "lon": -119.155},
  ...
}

Usage
-----
# Bounding box (south, west, north, east):
python scripts/fetch_addresses.py --bbox 34.83,-119.20,34.88,-119.10

# GeoJSON or WKT polygon file:
python scripts/fetch_addresses.py --poly boundary.geojson
python scripts/fetch_addresses.py --poly boundary.wkt

# Optional: specify output file (default: addresses.json)
python scripts/fetch_addresses.py --bbox 34.83,-119.20,34.88,-119.10 -o my_addresses.json

Dependencies
------------
Only the Python standard library is required.  No third-party packages needed.
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
REQUEST_TIMEOUT = 120   # seconds
RETRY_WAIT = 5          # seconds between retries on rate-limit (HTTP 429)
MAX_RETRIES = 3


# ── Overpass query helpers ────────────────────────────────────────────────────

def _build_bbox_query(south: float, west: float, north: float, east: float) -> str:
    """Return an Overpass QL query for addresses within a bounding box."""
    bbox = f"{south},{west},{north},{east}"
    return f"""
[out:json][timeout:60];
(
  node["addr:housenumber"]["addr:street"]({bbox});
  way["addr:housenumber"]["addr:street"]({bbox});
  relation["addr:housenumber"]["addr:street"]({bbox});
);
out center;
""".strip()


def _build_poly_query(poly_coords: list[tuple[float, float]]) -> str:
    """
    Return an Overpass QL query for addresses within a polygon.
    `poly_coords` is a list of (lat, lon) pairs forming the polygon boundary.
    """
    coord_str = " ".join(f"{lat} {lon}" for lat, lon in poly_coords)
    return f"""
[out:json][timeout:60];
(
  node["addr:housenumber"]["addr:street"](poly:"{coord_str}");
  way["addr:housenumber"]["addr:street"](poly:"{coord_str}");
  relation["addr:housenumber"]["addr:street"](poly:"{coord_str}");
);
out center;
""".strip()


def _run_overpass_query(query: str) -> dict:
    """POST query to Overpass API and return parsed JSON."""
    data = urllib.parse.urlencode({"data": query}).encode()
    req = urllib.request.Request(
        OVERPASS_URL,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < MAX_RETRIES:
                print(
                    f"  Rate-limited (HTTP 429). Waiting {RETRY_WAIT}s before retry "
                    f"{attempt}/{MAX_RETRIES}…",
                    file=sys.stderr,
                )
                time.sleep(RETRY_WAIT)
            else:
                raise


# ── Address extraction ────────────────────────────────────────────────────────

def _element_lat_lon(element: dict) -> tuple[float | None, float | None]:
    """
    Return (lat, lon) for an OSM element.
    Nodes have 'lat'/'lon' directly; ways/relations expose 'center'.
    """
    if element.get("type") == "node":
        return element.get("lat"), element.get("lon")
    center = element.get("center")
    if center:
        return center.get("lat"), center.get("lon")
    return None, None


def _format_address(tags: dict) -> str | None:
    """
    Build a human-readable address string from OSM address tags.
    Returns None if the essential tags are missing.
    """
    number = tags.get("addr:housenumber", "").strip()
    street = tags.get("addr:street", "").strip()
    if not number or not street:
        return None
    return f"{number} {street}"


def extract_addresses(overpass_data: dict) -> dict[str, dict]:
    """
    Parse Overpass API response and return a dict mapping address strings to
    {"lat": ..., "lon": ...} pairs.  Duplicate addresses keep the first entry.
    """
    addresses: dict[str, dict] = {}
    for element in overpass_data.get("elements", []):
        tags = element.get("tags", {})
        address = _format_address(tags)
        if not address:
            continue
        lat, lon = _element_lat_lon(element)
        if lat is None or lon is None:
            continue
        if address not in addresses:
            addresses[address] = {"lat": lat, "lon": lon}
    return addresses


# ── Boundary input parsing ────────────────────────────────────────────────────

def _parse_bbox(bbox_str: str) -> tuple[float, float, float, float]:
    """Parse 'south,west,north,east' string into a tuple of floats."""
    parts = [p.strip() for p in bbox_str.split(",")]
    if len(parts) != 4:
        raise ValueError(
            f"Expected 4 comma-separated values (south,west,north,east), got {len(parts)}."
        )
    try:
        south, west, north, east = [float(p) for p in parts]
    except ValueError as exc:
        raise ValueError(f"Could not parse bounding box values as floats: {exc}") from exc
    if south >= north:
        raise ValueError(f"south ({south}) must be less than north ({north}).")
    if west >= east:
        raise ValueError(f"west ({west}) must be less than east ({east}).")
    return south, west, north, east


def _parse_poly_file(path: str) -> list[tuple[float, float]]:
    """
    Read a polygon boundary file and return a list of (lat, lon) pairs.
    Supports:
      - GeoJSON (Feature or FeatureCollection with a Polygon geometry)
      - Plain JSON array of [lon, lat] or {lat, lon} objects
      - WKT POLYGON(...)
    """
    with open(path) as fh:
        raw = fh.read().strip()

    # Try JSON first
    try:
        obj = json.loads(raw)
        return _coords_from_json(obj)
    except (json.JSONDecodeError, ValueError):
        pass

    # Try WKT
    if raw.upper().startswith("POLYGON"):
        return _coords_from_wkt(raw)

    raise ValueError(
        f"Could not parse '{path}' as GeoJSON or WKT.  "
        "Expected a GeoJSON Polygon/Feature or a WKT POLYGON string."
    )


def _coords_from_json(obj) -> list[tuple[float, float]]:
    """Extract (lat, lon) pairs from various JSON shapes."""
    # FeatureCollection
    if isinstance(obj, dict) and obj.get("type") == "FeatureCollection":
        features = obj.get("features", [])
        if not features:
            raise ValueError("FeatureCollection has no features.")
        obj = features[0]

    # Feature
    if isinstance(obj, dict) and obj.get("type") == "Feature":
        obj = obj.get("geometry", {})

    # Geometry
    if isinstance(obj, dict) and obj.get("type") == "Polygon":
        ring = obj["coordinates"][0]  # outer ring
        return [(lat, lon) for lon, lat in ring]

    # Plain array of [lon, lat]
    if isinstance(obj, list) and obj and isinstance(obj[0], (list, tuple)) and len(obj[0]) == 2:
        # Heuristic: first element – if |val[0]| > 90 it's probably longitude first
        sample = obj[0]
        if abs(sample[0]) > 90:
            return [(lat, lon) for lon, lat in obj]
        return [(lat, lon) for lat, lon in obj]

    # Array of {lat, lon} objects
    if isinstance(obj, list) and obj and isinstance(obj[0], dict):
        if "lat" in obj[0] and "lon" in obj[0]:
            return [(p["lat"], p["lon"]) for p in obj]

    raise ValueError("Unrecognised JSON structure.  Expected GeoJSON Polygon, Feature, or array of coordinates.")


def _coords_from_wkt(wkt: str) -> list[tuple[float, float]]:
    """Parse a WKT POLYGON string into (lat, lon) pairs."""
    import re
    m = re.search(r"POLYGON\s*\(\s*\(([^)]+)\)", wkt, re.IGNORECASE)
    if not m:
        raise ValueError(f"Could not parse WKT polygon from: {wkt[:80]}")
    pairs = m.group(1).split(",")
    coords = []
    for pair in pairs:
        parts = pair.strip().split()
        if len(parts) < 2:
            raise ValueError(f"Bad coordinate pair in WKT: '{pair}'")
        lon, lat = float(parts[0]), float(parts[1])
        coords.append((lat, lon))
    return coords


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Fetch house addresses and lat/lon pairs from OpenStreetMap "
            "within a geographic boundary and write them to a JSON file."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    boundary = parser.add_mutually_exclusive_group(required=True)
    boundary.add_argument(
        "--bbox",
        metavar="S,W,N,E",
        help="Bounding box as south,west,north,east (decimal degrees).",
    )
    boundary.add_argument(
        "--poly",
        metavar="FILE",
        help="Path to a GeoJSON or WKT file describing the boundary polygon.",
    )

    parser.add_argument(
        "-o", "--output",
        metavar="FILE",
        default="addresses.json",
        help="Output JSON file path (default: addresses.json).",
    )

    args = parser.parse_args()

    # Build Overpass query
    if args.bbox:
        print(f"Bounding box: {args.bbox}")
        try:
            south, west, north, east = _parse_bbox(args.bbox)
        except ValueError as exc:
            parser.error(str(exc))
        query = _build_bbox_query(south, west, north, east)
    else:
        print(f"Reading boundary from: {args.poly}")
        try:
            poly_coords = _parse_poly_file(args.poly)
        except (ValueError, OSError) as exc:
            parser.error(str(exc))
        query = _build_poly_query(poly_coords)

    # Query Overpass API
    print("Querying Overpass API…")
    try:
        data = _run_overpass_query(query)
    except urllib.error.URLError as exc:
        print(f"Network error: {exc}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.HTTPError as exc:
        print(f"HTTP error {exc.code}: {exc.reason}", file=sys.stderr)
        sys.exit(1)

    # Extract and deduplicate addresses
    addresses = extract_addresses(data)
    print(f"Found {len(addresses)} unique addresses.")

    # Write output
    with open(args.output, "w", encoding="utf-8") as fh:
        json.dump(addresses, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    print(f"Written to {args.output}")


if __name__ == "__main__":
    main()
