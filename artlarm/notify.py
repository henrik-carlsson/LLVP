"""Skickar ett larm på alla kanaler (SMS och/eller e-post) som prenumerationen har."""
from typing import Any, Dict, Optional

import db
from email_sender import EmailSender, default_email_sender
from sms import SmsSender, default_sender


class Notifier:
    def __init__(self, sms: Optional[SmsSender] = None, email: Optional[EmailSender] = None):
        self.sms, self.email = sms, email

    def send(self, sub: Dict[str, Any], message: str, subject: str) -> None:
        """Försöker alla kanaler; kastar fel om någon misslyckades (då görs ett nytt försök
        senare, och en kanal som redan lyckats kan få larmet en gång till)."""
        errors = []
        for send in (
            (lambda: self.sms.send(sub["phone"], message)) if sub.get("phone") and self.sms else None,
            *((lambda to=to: self.email.send(to, subject, message))
              for to in (db.split_emails(sub.get("email", "")) if self.email else [])),
        ):
            if send:
                try:
                    send()
                except Exception as e:  # noqa: BLE001
                    errors.append(e)
        if errors:
            raise errors[0]


def default_notifier() -> Notifier:
    return Notifier(sms=default_sender(), email=default_email_sender())
