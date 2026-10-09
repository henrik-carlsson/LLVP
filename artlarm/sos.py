"""Klient mot Artdatabankens Species Observation System (SOS) som levererar Artportalen-fynd.

Fältnamn följer https://github.com/biodiversitydata-se/SOS (Docs/SearchFilter.md).
"""
import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import httpx

import config

PAGE_SIZE = 1000


@dataclass
class Observation:
    occurrence_id: str
    taxon: str          # svenskt namn, annars vetenskapligt
    observed_at: datetime
    sighting_id: Optional[str]  # Artportalen-id, bara för fynd från Artportalen
    source_url: str = ""        # fynd från andra källor (t.ex. iNaturalist) har id:t som URL

    @property
    def url(self) -> str:
        if self.sighting_id:
            return config.ARTPORTALEN_SIGHTING_URL.format(id=self.sighting_id)
        return self.source_url


def parse_observation(rec: Dict[str, Any]) -> Optional[Observation]:
    occ = (rec.get("occurrence") or {}).get("occurrenceId")
    start = (rec.get("event") or {}).get("startDate")
    if not occ or not start:
        return None
    taxon = rec.get("taxon") or {}
    name = taxon.get("vernacularName") or taxon.get("scientificName") or "Okänd art"
    # SOS levererar flera källor. Artportalen: urn:lsid:artportalen.se:sighting:12345,
    # iNaturalist m.fl.: id:t är en https-URL till fyndet.
    m = re.fullmatch(r"urn:lsid:artportalen\.se:sighting:(\d+)", occ, re.IGNORECASE)
    return Observation(
        occurrence_id=occ,
        taxon=name[:1].upper() + name[1:],
        observed_at=datetime.fromisoformat(start.replace("Z", "+00:00")),
        sighting_id=m.group(1) if m else None,
        source_url=occ if occ.startswith("https://") else "",
    )


class SosClient:
    def __init__(self, http: Optional[httpx.Client] = None):
        self.http = http or httpx.Client(timeout=30)

    def search(
        self,
        geometry: Dict[str, Any],
        observed_from: Optional[date] = None,
        modified_from: Optional[date] = None,
    ) -> List[Observation]:
        """Hämtar observationer inom geometrin (alla sidor). MultiPolygon söks del för del."""
        parts = (
            [{"type": "polygon", "coordinates": c} for c in geometry["coordinates"]]
            if geometry["type"].lower() == "multipolygon"
            else [{"type": "polygon", "coordinates": geometry["coordinates"]}]
        )
        seen: Dict[str, Observation] = {}
        for part in parts:
            for o in self._search_polygon(part, observed_from, modified_from):
                seen.setdefault(o.occurrence_id, o)
        return list(seen.values())

    def _search_polygon(
        self,
        geometry: Dict[str, Any],
        observed_from: Optional[date],
        modified_from: Optional[date],
    ) -> List[Observation]:
        body: Dict[str, Any] = {
            "geographics": {"geometries": [geometry], "considerObservationAccuracy": False},
            "output": {"fields": ["occurrence.occurrenceId", "event.startDate",
                                  "taxon.vernacularName", "taxon.scientificName"]},
        }
        if observed_from:
            body["date"] = {"startDate": observed_from.isoformat(),
                            "dateFilterType": "OverlappingStartDateAndEndDate"}
        if modified_from:
            body["modifiedDate"] = {"from": modified_from.isoformat()}

        out: List[Observation] = []
        skip = 0
        while True:
            r = self.http.post(
                f"{config.SOS_BASE_URL}/Observations/Search",
                params={"skip": skip, "take": PAGE_SIZE},
                json=body,
                headers={"Ocp-Apim-Subscription-Key": config.SOS_API_KEY},
            )
            r.raise_for_status()
            data = r.json()
            records = data.get("records", [])
            out.extend(o for o in map(parse_observation, records) if o)
            skip += PAGE_SIZE
            if skip >= data.get("totalCount", 0) or not records:
                return out
