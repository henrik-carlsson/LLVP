"""E-postutskick via SMTP (STARTTLS), eller loggning vid torrkörning."""
import logging
import smtplib
from email.message import EmailMessage
from typing import List, Tuple

import config

log = logging.getLogger("artlarm.email")


class EmailSender:
    def send(self, to: str, subject: str, body: str) -> None:
        raise NotImplementedError


class LogEmailSender(EmailSender):
    def __init__(self):
        self.sent: List[Tuple[str, str, str]] = []

    def send(self, to: str, subject: str, body: str) -> None:
        self.sent.append((to, subject, body))
        log.info("E-post (torrkörning) till %s: %s | %s", to, subject, body)


class SmtpSender(EmailSender):
    def send(self, to: str, subject: str, body: str) -> None:
        msg = EmailMessage()
        msg["From"], msg["To"], msg["Subject"] = config.EMAIL_FROM, to, subject
        msg.set_content(body)
        if config.SMTP_PORT == 465:  # implicit SSL
            smtp = smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT, timeout=30)
        else:  # STARTTLS
            smtp = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=30)
            smtp.starttls()
        with smtp as s:
            if config.SMTP_USER:
                s.login(config.SMTP_USER, config.SMTP_PASSWORD)
            s.send_message(msg)


def default_email_sender() -> EmailSender:
    if config.SMTP_HOST:
        return SmtpSender()
    log.warning("SMTP_HOST saknas – e-post skickas inte på riktigt.")
    return LogEmailSender()
