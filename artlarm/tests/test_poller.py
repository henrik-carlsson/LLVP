import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient

import config
import db
import poller
from app import create_app
from email_sender import LogEmailSender
from notify import Notifier
from sms import LogSender
from sos import Observation, parse_observation

POLY = {"type": "Polygon", "coordinates": [[[15, 58], [15, 59], [16, 59], [15, 58]]]}


class FakeSos:
    def __init__(self, obs):
        self.obs, self.calls = obs, []

    def search(self, geometry, observed_from=None, modified_from=None):
        self.calls.append((observed_from, modified_from))
        return list(self.obs)


def ob(n, when="2026-10-01T10:30:00"):
    return Observation(f"urn:lsid:artportalen.se:Sighting:{n}", "Storspov",
                       datetime.fromisoformat(when), str(n))


@pytest.fixture
def con():
    return db.connect(":memory:")


def make(con, start="2026-09-01"):
    sid = db.add_subscription(con, "+46701234567", start, [{"name": "Gården", "geometry": POLY}])
    return db.get_subscription(con, sid)


def test_message_contains_type_time_property_and_link():
    msg = poller.format_alert(ob(123), "Gården")
    assert msg == "Storspov, 2026-10-01 10:30, Gården. https://www.artportalen.se/Sighting/123"


def test_backfill_then_no_duplicates(con):
    sub, sms = make(con), LogSender()
    sos = FakeSos([ob(1), ob(2)])
    today = date(2026, 10, 8)
    assert poller.poll_subscription(con, sos, Notifier(sms), sub, today) == 2
    assert sos.calls[0] == (date(2026, 9, 1), None)  # bakåtblick från startdatum
    sub = db.get_subscription(con, sub["id"])
    assert poller.poll_subscription(con, sos, Notifier(sms), sub, today) == 0  # dedupe
    assert sos.calls[1] == (None, date(2026, 10, 7))  # därefter inkrementell
    assert len(sms.sent) == 2


def test_new_observation_alerts_later(con):
    sub, sms = make(con), LogSender()
    sos = FakeSos([ob(1)])
    poller.poll_subscription(con, sos, Notifier(sms), sub, date(2026, 10, 8))
    sos.obs.append(ob(2, "2026-10-08T08:00:00"))
    sub = db.get_subscription(con, sub["id"])
    assert poller.poll_subscription(con, sos, Notifier(sms), sub, date(2026, 10, 8)) == 1
    assert "Sighting/2" in sms.sent[-1][1]


def test_future_start_date_sends_nothing_and_does_not_call_api(con):
    sub, sms, sos = make(con, "2026-12-01"), LogSender(), FakeSos([ob(1)])
    assert poller.poll_subscription(con, sos, Notifier(sms), sub, date(2026, 10, 8)) == 0
    assert sos.calls == [] and sms.sent == []


def test_observations_before_start_date_ignored_when_modified(con):
    sub, sms = make(con, "2026-10-05"), LogSender()
    sos = FakeSos([ob(1, "2026-10-01T10:00:00")])
    assert poller.poll_subscription(con, sos, Notifier(sms), sub, date(2026, 10, 8)) == 0


def test_large_backfill_is_summarised(con, monkeypatch):
    monkeypatch.setattr(config, "MAX_SMS_PER_RUN", 2)
    sub, sms = make(con), LogSender()
    sos = FakeSos([ob(i, f"2026-10-0{i}T10:00:00") for i in range(1, 6)])
    poller.poll_subscription(con, sos, Notifier(sms), sub, date(2026, 10, 8))
    assert len(sms.sent) == 3 and "3 äldre" in sms.sent[0][1]


def test_failed_sms_is_retried(con):
    class Flaky(LogSender):
        fail = True

        def send(self, to, message):
            if self.fail:
                raise RuntimeError("nere")
            super().send(to, message)

    sub, sms, sos = make(con), Flaky(), FakeSos([ob(1)])
    assert poller.poll_subscription(con, sos, Notifier(sms), sub, date(2026, 10, 8)) == 0
    sms.fail = False
    sub = db.get_subscription(con, sub["id"])
    assert poller.poll_subscription(con, sos, Notifier(sms), sub, date(2026, 10, 8)) == 1


def test_parse_observation():
    o = parse_observation({"occurrence": {"occurrenceId": "urn:lsid:artportalen.se:Sighting:99"},
                           "event": {"startDate": "2026-10-01T10:30:00+02:00"},
                           "taxon": {"vernacularName": "gök", "scientificName": "Cuculus canorus"}})
    assert o.taxon == "Gök" and o.url.endswith("/Sighting/99")


def test_api_create_validates_and_backfills(con):
    sms = LogSender()
    client = TestClient(create_app(con, FakeSos([ob(1)]), Notifier(sms),
                                   resolver=fastighet.UnconfiguredResolver(), run_poller=False))
    r = client.post("/api/subscriptions", json={
        "phone": "070-123 45 67", "start_date": "2026-09-01",
        "properties": [{"name": "Gården", "geometry": POLY}]})
    assert r.status_code == 201 and r.json()["phone"] == "+46701234567"
    assert len(sms.sent) == 1  # bakgrundsjobbet körs innan svaret lämnar testklienten
    r = client.post("/api/subscriptions", json={
        "phone": "070-123 45 67", "start_date": "2026-09-01",
        "properties": [{"name": "X", "designation": "Uppsala Gamla Uppsala 1:1"}]})
    assert r.status_code == 501
    assert client.post("/api/subscriptions", json={
        "phone": "abc", "start_date": "2026-09-01", "properties": []}).status_code == 422


def test_email_only_and_both_channels(con):
    sms, mail = LogSender(), LogEmailSender()
    sid = db.add_subscription(con, "", "2026-09-01", [{"name": "Gården", "geometry": POLY}],
                              email="a@b.se")
    sub = db.get_subscription(con, sid)
    poller.poll_subscription(con, FakeSos([ob(1)]), Notifier(sms, mail), sub, date(2026, 10, 8))
    assert sms.sent == [] and len(mail.sent) == 1
    to, subject, body = mail.sent[0]
    assert to == "a@b.se" and subject == "Artlarm: Storspov – Gården" and "Sighting/1" in body
    sid2 = db.add_subscription(con, "+46701234567", "2026-09-01",
                               [{"name": "Gården", "geometry": POLY}], email="a@b.se")
    poller.poll_subscription(con, FakeSos([ob(1)]), Notifier(sms, mail),
                             db.get_subscription(con, sid2), date(2026, 10, 8))
    assert len(sms.sent) == 1 and len(mail.sent) == 2


def test_api_requires_a_channel_and_validates_email(con):
    client = TestClient(create_app(con, FakeSos([]), Notifier(LogSender()), run_poller=False))
    base = {"start_date": "2026-09-01", "properties": [{"name": "G", "geometry": POLY}]}
    assert client.post("/api/subscriptions", json=base).status_code == 422
    assert client.post("/api/subscriptions", json={**base, "email": "nej"}).status_code == 422
    r = client.post("/api/subscriptions", json={**base, "email": "a@b.se"})
    assert r.status_code == 201 and r.json()["phone"] == ""


def test_non_artportalen_sources_link_to_their_own_url():
    o = parse_observation({"occurrence": {"occurrenceId": "https://www.inaturalist.org/observations/402181305"},
                           "event": {"startDate": "2026-09-20T17:10:05+02:00"},
                           "taxon": {"scientificName": "Coprinellus"}})
    assert o.url == "https://www.inaturalist.org/observations/402181305" and o.sighting_id is None
    o = parse_observation({"occurrence": {"occurrenceId": "urn:lsid:artportalen.se:sighting:136494510"},
                           "event": {"startDate": "2026-09-10T00:00:00+02:00"},
                           "taxon": {"scientificName": "Sparassis crispa", "vernacularName": "blomkålssvamp"}})
    assert o.url == "https://www.artportalen.se/Sighting/136494510" and o.taxon == "Blomkålssvamp"


# --- Lantmäteriet-uppslag (mockad HTTP) ---
import httpx
import fastighet


def _feat(kommun, trakt, block, enhet, ref, coords):
    return {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [coords]},
            "properties": {"kommunnamn": kommun, "trakt": trakt, "block": block, "enhet": enhet,
                           "registerenhetsreferens": ref}}


SQ1 = [[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]
SQ2 = [[1, 0], [1, 1], [2, 1], [2, 0], [1, 0]]


def _resolver(db_features, calls):
    def handler(req):
        p = dict(req.url.params)
        calls.append(p)
        hit = [f for f in db_features
               if f["properties"]["trakt"] == p.get("trakt") and f["properties"]["block"] == p.get("block")
               and str(f["properties"]["enhet"]) == p.get("enhet")
               and ("kommunnamn" not in p or f["properties"]["kommunnamn"] == p["kommunnamn"])]
        return httpx.Response(200, json={"features": hit})
    return fastighet.LantmaterietResolver(httpx.Client(transport=httpx.MockTransport(handler)))


def test_parse_designation():
    assert fastighet.parse_designation("Mora Östra Storbyn 85:1") == ("MORA ÖSTRA STORBYN", "85", 1)
    assert fastighet.parse_designation("ÖSTRA_STORBYN_85_1") == ("ÖSTRA STORBYN", "85", 1)
    with pytest.raises(ValueError):
        fastighet.parse_designation("bara text")


def test_resolver_merges_areas_and_handles_municipality_prefix():
    feats = [_feat("MORA", "ÖSTRA STORBYN", "85", 1, "r1", SQ1), _feat("MORA", "ÖSTRA STORBYN", "85", 1, "r1", SQ2)]
    g = _resolver(feats, []).resolve("Mora Östra Storbyn 85:1")
    assert g["type"] == "Polygon"  # intilliggande områden slås ihop
    assert _resolver(feats, []).resolve("östra storbyn 85:1")["type"] == "Polygon"


def test_resolver_not_found_and_ambiguous():
    r = _resolver([], [])
    with pytest.raises(fastighet.PropertyNotFound):
        r.resolve("Okänd 1:1")
    feats = [_feat("MORA", "X", "1", 1, "a", SQ1), _feat("ORSA", "X", "1", 1, "b", SQ2)]
    with pytest.raises(fastighet.AmbiguousProperty) as e:
        _resolver(feats, []).resolve("X 1:1")
    assert "Mora" in str(e.value) and "Orsa" in str(e.value)
    assert _resolver(feats, []).resolve("Orsa X 1:1")["type"] == "Polygon"


def test_api_designation_uses_resolver(con):
    feats = [_feat("MORA", "ÖSTRA STORBYN", "85", 1, "r1", SQ1)]
    sms = LogSender()
    client = TestClient(create_app(con, FakeSos([ob(1)]), Notifier(sms),
                                   resolver=_resolver(feats, []), run_poller=False))
    base = {"phone": "070-123 45 67", "start_date": "2026-09-01"}
    r = client.post("/api/subscriptions", json={**base, "properties": [{"name": "G", "designation": "Östra Storbyn 85:1"}]})
    assert r.status_code == 201 and len(sms.sent) == 1
    r = client.post("/api/subscriptions", json={**base, "properties": [{"name": "G", "designation": "Saknas 1:1"}]})
    assert r.status_code == 404


# --- Noggrannhet / osäkert läge ---
from shapely.geometry import box, mapping as _mapping
from pyproj import Transformer as _T

_to_wgs = _T.from_crs("EPSG:3006", "EPSG:4326", always_xy=True).transform
# fastighet = ruta 100x100 m i SWEREF 99 TM (Dalarna)
_E, _N = 465000, 6790000
_SQUARE = {"type": "Polygon", "coordinates": [[list(_to_wgs(_E + dx, _N + dy)) for dx, dy in
                                                ((0, 0), (0, 100), (100, 100), (100, 0), (0, 0))]]}


def _at(e, n, unc, occ="1"):
    lon, lat = _to_wgs(e, n)
    return Observation(f"urn:lsid:artportalen.se:Sighting:{occ}", "Gök",
                       datetime(2026, 10, 1, 10, 0), occ, lat=lat, lon=lon, uncertainty_m=unc)


def test_inside_is_unmarked_and_nearby_is_marked_and_far_or_vague_dropped():
    found = [
        _at(_E + 50, _N + 50, 10, "1"),      # inne
        _at(_E + 150, _N + 50, 100, "2"),    # 50 m utanför, osäkerhet 100 m -> märks
        _at(_E + 400, _N + 50, 100, "3"),    # 300 m utanför, osäkerhet 100 m -> bort
        _at(_E + 150, _N + 50, 5000, "4"),   # för osäker (>500 m) -> bort
    ]
    out = {o.sighting_id: o for o in poller.apply_location_accuracy(found, _SQUARE)}
    assert set(out) == {"1", "2"}
    assert out["1"].location_note == ""
    assert "ca 50 m utanför" in out["2"].location_note and "±100 m" in out["2"].location_note
    assert poller.format_alert(out["2"], "Gården").startswith("Gök, 2026-10-01 10:00, Gården [OSÄKERT LÄGE")


def test_marked_alert_reaches_email_subject(con):
    mail, sms = LogEmailSender(), LogSender()
    sid = db.add_subscription(con, "", "2026-09-01", [{"name": "Gården", "geometry": _SQUARE}], email="a@b.se")
    poller.poll_subscription(con, FakeSos([_at(_E + 150, _N + 50, 100)]), Notifier(sms, mail),
                             db.get_subscription(con, sid), date(2026, 10, 8))
    to, subject, body = mail.sent[0]
    assert subject.startswith("Artlarm (osäkert läge):") and "OSÄKERT LÄGE" in body


# --- Dygnssammanfattning ---
import digest
from datetime import timezone as _tz

UTC = _tz.utc


def _mail_db(con, emails_props):
    for email, names in emails_props:
        db.add_subscription(con, "", "2026-01-01",
                            [{"name": n, "geometry": POLY} for n in names], email=email)


def test_digest_one_mail_per_address_even_with_several_subscriptions(con):
    _mail_db(con, [("a@b.se", ["Gård A"]), ("a@b.se", ["Gård B"]), ("c@d.se", ["Gård C"])])
    mail = LogEmailSender()
    # Dag 1: adresserna seedas, inget skickas
    day1 = datetime(2026, 10, 22, 14, 0, tzinfo=UTC)
    assert digest.send_due_digests(con, mail, day1) == 0
    # Larm skickas under dygnet
    db.mark_sent(con, 1, "x1", "Storspov, 2026-10-22 10:00, Gård A. https://x/1")
    con.execute("UPDATE sent_alerts SET sent_at = '2026-10-22T16:00:00+00:00'"); con.commit()
    # Före 09:00 svensk tid: inget
    assert digest.send_due_digests(con, mail, datetime(2026, 10, 23, 6, 30, tzinfo=UTC)) == 0  # 08:30 svensk tid
    # 09:00 svensk tid (07:00 UTC, sommartid slut → 08:00 UTC): skickas, ett per adress
    now = datetime(2026, 10, 23, 8, 0, tzinfo=UTC)
    assert digest.send_due_digests(con, mail, now) == 2
    to = {m[0]: m for m in mail.sent}
    assert set(to) == {"a@b.se", "c@d.se"}
    _, subj, body = to["a@b.se"]
    assert "1 ny observation" in subj and "Gård A: 1 nya" in body and "Storspov" in body and "Gård B: inga nya" in body
    assert "inga nya observationer" in to["c@d.se"][1]
    # inte två gånger samma dag
    assert digest.send_due_digests(con, mail, datetime(2026, 10, 23, 12, 0, tzinfo=UTC)) == 0
    # nästa dag skickas även om inget registrerats
    assert digest.send_due_digests(con, mail, datetime(2026, 10, 24, 8, 0, tzinfo=UTC)) == 2
    assert "inga nya observationer" in mail.sent[-1][1] and "Storspov" not in mail.sent[-1][2]


def test_digest_failure_is_retried_and_phone_only_gets_none(con):
    _mail_db(con, [("a@b.se", ["Gård A"])])
    db.add_subscription(con, "+46701234567", "2026-01-01", [{"name": "P", "geometry": POLY}])

    class Flaky(LogEmailSender):
        fail = True

        def send(self, *a):
            if self.fail:
                raise RuntimeError("nere")
            super().send(*a)

    mail = Flaky()
    digest.send_due_digests(con, mail, datetime(2026, 10, 22, 14, 0, tzinfo=UTC))
    t = datetime(2026, 10, 23, 8, 0, tzinfo=UTC)
    assert digest.send_due_digests(con, mail, t) == 0
    mail.fail = False
    assert digest.send_due_digests(con, mail, t) == 1 and len(mail.sent) == 1
