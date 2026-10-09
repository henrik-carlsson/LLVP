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
    client = TestClient(create_app(con, FakeSos([ob(1)]), Notifier(sms), run_poller=False))
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
