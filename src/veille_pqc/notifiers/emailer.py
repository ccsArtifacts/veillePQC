from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from pathlib import Path


def send_email_with_attachment(subject: str, body: str, to_email: str, attachment_path: str | None = None) -> None:
    smtp_host = os.getenv("VEILLE_SMTP_HOST")
    smtp_port = int(os.getenv("VEILLE_SMTP_PORT", "587"))
    smtp_user = os.getenv("VEILLE_SMTP_USER")
    smtp_password = os.getenv("VEILLE_SMTP_PASSWORD")
    smtp_from = os.getenv("VEILLE_SMTP_FROM", smtp_user or "")
    use_starttls = os.getenv("VEILLE_SMTP_STARTTLS", "true").lower() == "true"

    missing = [name for name, value in {
        "VEILLE_SMTP_HOST": smtp_host,
        "VEILLE_SMTP_USER": smtp_user,
        "VEILLE_SMTP_PASSWORD": smtp_password,
        "VEILLE_SMTP_FROM": smtp_from,
    }.items() if not value]
    if missing:
        raise RuntimeError(f"Variables SMTP manquantes: {', '.join(missing)}")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = smtp_from
    msg["To"] = to_email
    msg.set_content(body)

    if attachment_path:
        path = Path(attachment_path)
        msg.add_attachment(
            path.read_bytes(),
            maintype="text",
            subtype="markdown" if path.suffix.lower() == ".md" else "plain",
            filename=path.name,
        )

    with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
        if use_starttls:
            server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
