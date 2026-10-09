"""SMS-utskick. 46elks när nycklar finns, annars loggning (torrkörning)."""
import logging
from typing import List, Optional, Tuple

import httpx

import config

log = logging.getLogger("artlarm.sms")


class SmsSender:
    def send(self, to: str, message: str) -> None:
        raise NotImplementedError


class LogSender(SmsSender):
    def __init__(self):
        self.sent: List[Tuple[str, str]] = []

    def send(self, to: str, message: str) -> None:
        self.sent.append((to, message))
        log.info("SMS (torrkörning) till %s: %s", to, message)


class ElksSender(SmsSender):
    URL = "https://api.46elks.com/a1/sms"

    def __init__(self, user: str, password: str, sender: str, http: Optional[httpx.Client] = None):
        self.auth, self.sender = (user, password), sender
        self.http = http or httpx.Client(timeout=30)

    def send(self, to: str, message: str) -> None:
        r = self.http.post(self.URL, auth=self.auth,
                           data={"from": self.sender, "to": to, "message": message})
        r.raise_for_status()


def default_sender() -> SmsSender:
    if config.ELKS_USER and config.ELKS_PASSWORD:
        return ElksSender(config.ELKS_USER, config.ELKS_PASSWORD, config.SMS_SENDER)
    log.warning("ELKS_USER/ELKS_PASSWORD saknas – SMS skickas inte på riktigt.")
    return LogSender()
