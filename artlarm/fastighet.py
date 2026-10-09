"""Fastighet -> geometri.

Stöd finns för att ange en GeoJSON-polygon direkt. Uppslag via fastighetsbeteckning
(Lantmäteriets fastighetsdata) görs via `PropertyResolver`; en riktig implementation
kräver avtal/nyckel hos Lantmäteriet och är ännu inte kopplad.
"""
from typing import Any, Dict


class PropertyNotFound(Exception):
    pass


class ResolverNotConfigured(Exception):
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
