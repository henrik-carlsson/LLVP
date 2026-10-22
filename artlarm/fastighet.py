"""Fastighet -> geometri.

Geometri kan anges direkt (GeoJSON) eller slås upp via fastighetsbeteckning mot
Lantmäteriets fastighetsindelning (`LantmaterietResolver`).
"""
import re
from typing import Any, Dict, List, Optional

import httpx
from shapely.geometry import mapping, shape
from shapely.ops import unary_union

import config


class PropertyNotFound(Exception):
    pass


class ResolverNotConfigured(Exception):
    pass


class AmbiguousProperty(Exception):
    pass


def validate_geometry(geom: Dict[str, Any]) -> Dict[str, Any]:
    if geom.get("type") not in ("Polygon", "MultiPolygon") or not geom.get("coordinates"):
        raise ValueError("Geometrin måste vara en GeoJSON Polygon eller MultiPolygon (WGS84)")
    return geom


class PropertyResolver:
    def resolve(self, designation: str) -> Dict[str, Any]:
        """Returnerar GeoJSON (WGS84) för en fastighetsbeteckning, t.ex. 'Uppsala Gamla Uppsala 1:1'."""
        raise NotImplementedError


class UnconfiguredResolver(PropertyResolver):
    def resolve(self, designation: str) -> Dict[str, Any]:
        raise ResolverNotConfigured(
            "Uppslag via fastighetsbeteckning är inte konfigurerat (kräver Lantmäteriets API). "
            "Ange geometry (GeoJSON) tills vidare."
        )


def parse_designation(text: str) -> tuple:
    """'Mora Östra Storbyn 85:1' -> ('MORA ÖSTRA STORBYN', '85', 1). Även 'ÖSTRA_STORBYN_85_1'."""
    s = re.sub(r"[\s_]+", " ", text.strip()).upper()
    m = re.fullmatch(r"(.+?) (\S+?)[: ](\d+)", s)
    if not m:
        raise ValueError(f"Kan inte tolka fastighetsbeteckningen '{text}' (förväntat: [Kommun] Trakt Block:Enhet)")
    return m.group(1), m.group(2), int(m.group(3))


class LantmaterietResolver(PropertyResolver):
    """Slår upp en registerenhets samtliga områden och slår ihop dem till en geometri."""

    def __init__(self, http: Optional[httpx.Client] = None):
        self.http = http or httpx.Client(
            timeout=30, auth=(config.LM_CONSUMER_KEY, config.LM_CONSUMER_SECRET)
        )

    def _items(self, **params) -> List[Dict[str, Any]]:
        r = self.http.get(
            f"{config.LM_BASE_URL}/collections/registerenhetsomradesytor/items",
            params={**params, "limit": 1000},
            headers={"Accept": "application/geo+json"},
        )
        r.raise_for_status()
        return r.json().get("features", [])

    def resolve(self, designation: str) -> Dict[str, Any]:
        head, block, unit = parse_designation(designation)
        words = head.split()
        feats: List[Dict[str, Any]] = []
        # Först utan kommun, sedan med 1..n inledande ord som kommunnamn.
        for i in range(0, len(words)):
            params = {"trakt": " ".join(words[i:]), "block": block, "enhet": unit}
            if i:
                params["kommunnamn"] = " ".join(words[:i])
            feats = self._items(**params)
            if feats:
                break
        if not feats:
            raise PropertyNotFound(designation)
        refs = {f["properties"]["registerenhetsreferens"] for f in feats}
        if len(refs) > 1:
            names = sorted({f"{f['properties']['kommunnamn'].title()} {f['properties']['trakt'].title()} "
                            f"{f['properties']['block']}:{f['properties']['enhet']}" for f in feats})
            raise AmbiguousProperty("Beteckningen är flertydig, ange kommun: " + "; ".join(names))
        merged = unary_union([shape(f["geometry"]) for f in feats])
        return mapping(merged)


def default_resolver() -> PropertyResolver:
    if config.LM_CONSUMER_KEY and config.LM_CONSUMER_SECRET:
        return LantmaterietResolver()
    return UnconfiguredResolver()
