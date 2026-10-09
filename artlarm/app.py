"""FastAPI-tjänst: REST-API, enkelt webbgränssnitt och bakgrundspollning."""
import asyncio
import logging
import re
from contextlib import asynccontextmanager
from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator, model_validator

import config
import db
import fastighet
import poller
from notify import default_notifier
from sos import SosClient

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("artlarm")


class PropertyIn(BaseModel):
    name: str
    designation: Optional[str] = None       # fastighetsbeteckning (kräver Lantmäteri-koppling)
    geometry: Optional[Dict[str, Any]] = None  # GeoJSON Polygon/MultiPolygon, WGS84


class SubscriptionIn(BaseModel):
    phone: Optional[str] = None
    email: Optional[str] = None
    start_date: date
    properties: List[PropertyIn]

    @field_validator("phone")
    @classmethod
    def _e164(cls, v: Optional[str]) -> Optional[str]:
        if not v or not v.strip():
            return None
        v = re.sub(r"[ \-]", "", v)
        if v.startswith("00"):
            v = "+" + v[2:]
        elif v.startswith("0"):
            v = "+46" + v[1:]
        if not re.fullmatch(r"\+\d{8,15}", v):
            raise ValueError("Ogiltigt telefonnummer (t.ex. 070-123 45 67 eller +46701234567)")
        return v

    @field_validator("email")
    @classmethod
    def _email(cls, v: Optional[str]) -> Optional[str]:
        if not v or not v.strip():
            return None
        v = v.strip()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", v):
            raise ValueError("Ogiltig e-postadress")
        return v

    @model_validator(mode="after")
    def _channel(self):
        if not self.phone and not self.email:
            raise ValueError("Ange telefonnummer och/eller e-postadress")
        return self

    @field_validator("properties")
    @classmethod
    def _nonempty(cls, v):
        if not v:
            raise ValueError("Minst en fastighet krävs")
        return v


def create_app(con=None, sos=None, sender=None, resolver=None, run_poller: bool = True) -> FastAPI:
    con = con or db.connect(config.DB_PATH)
    sos = sos or SosClient()
    sender = sender or default_notifier()
    resolver = resolver or fastighet.UnconfiguredResolver()

    async def loop():
        while True:
            try:
                await asyncio.to_thread(poller.poll_all, con, sos, sender)
            except Exception:
                log.exception("Pollning misslyckades")
            await asyncio.sleep(config.POLL_SECONDS)

    @asynccontextmanager
    async def lifespan(_):
        task = asyncio.create_task(loop()) if run_poller else None
        yield
        if task:
            task.cancel()

    app = FastAPI(title="Artlarm", lifespan=lifespan)

    @app.get("/")
    def index():
        return FileResponse("static/index.html")

    @app.post("/api/subscriptions", status_code=201)
    def create(sub: SubscriptionIn, background: BackgroundTasks):
        props = []
        for p in sub.properties:
            try:
                geom = p.geometry or (resolver.resolve(p.designation) if p.designation else None)
                if geom is None:
                    raise ValueError(f"'{p.name}': ange geometry eller designation")
                props.append({"name": p.name, "geometry": fastighet.validate_geometry(geom)})
            except fastighet.ResolverNotConfigured as e:
                raise HTTPException(501, str(e))
            except fastighet.PropertyNotFound:
                raise HTTPException(404, f"Fastigheten '{p.designation}' hittades inte")
            except ValueError as e:
                raise HTTPException(422, str(e))
        sub_id = db.add_subscription(con, sub.phone or "", sub.start_date.isoformat(), props,
                                     email=sub.email or "")
        # Bakåtblickande larm direkt, utan att blockera svaret.
        background.add_task(lambda: poller.poll_subscription(con, sos, sender, db.get_subscription(con, sub_id)))
        return db.get_subscription(con, sub_id)

    @app.get("/api/subscriptions")
    def list_():
        return db.list_subscriptions(con)

    @app.delete("/api/subscriptions/{sub_id}", status_code=204)
    def delete(sub_id: int):
        if not db.delete_subscription(con, sub_id):
            raise HTTPException(404, "Prenumerationen finns inte")

    return app


app = None


def get_app() -> FastAPI:  # uvicorn app:get_app --factory
    return create_app()
