"""Läser en Forestand-fil (SS 637009 / GML) och returnerar fastighetens sammanslagna geometri.

Koordinaterna i filen är SWEREF 99 TM (EPSG:3006) och projiceras till WGS84 för SOS-API:t.
"""
import json
import xml.etree.ElementTree as ET
from typing import Any, Dict, List

from pyproj import Transformer
from shapely.geometry import Polygon, mapping
from shapely.ops import transform, unary_union

GML = "{http://www.opengis.net/gml/3.2}"


def _ring(el) -> List[tuple]:
    nums = [float(v) for v in el.find(f".//{GML}posList").text.split()]
    return list(zip(nums[0::2], nums[1::2]))


def load_geometry(path: str, srs: str = "EPSG:3006") -> Dict[str, Any]:
    """Slår ihop alla polygoner i filen till en GeoJSON-geometri (WGS84)."""
    polys = []
    for poly in ET.parse(path).getroot().iter(f"{GML}Polygon"):
        exterior = _ring(poly.find(f"{GML}exterior"))
        holes = [_ring(i) for i in poly.findall(f"{GML}interior")]
        polys.append(Polygon(exterior, holes).buffer(0))  # buffer(0) lagar ogiltiga ringar
    if not polys:
        raise ValueError("Inga polygoner hittades i filen")
    merged = unary_union(polys)
    to_wgs = Transformer.from_crs(srs, "EPSG:4326", always_xy=True).transform
    return json.loads(json.dumps(mapping(transform(to_wgs, merged))))
