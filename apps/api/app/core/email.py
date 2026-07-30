"""Outbound email for password-reset and verification links.

Real SMTP is entirely optional (`smtp_host` unset): the response
requirements for this feature were "build the full flow now, wire in a real
mail provider later" — so with no provider configured, the message is
logged rather than sent. Every reset/verify endpoint works end-to-end
either way; only the delivery mechanism differs. Set every `smtp_*` setting
to switch a deployment over to real delivery with no code change.
"""
import smtplib
from email.message import EmailMessage

import structlog

from app.core.config import get_settings

logger = structlog.get_logger(__name__)


def send_email(to: str, subject: str, body: str) -> None:
    settings = get_settings()
    if not settings.smtp_host:
        logger.info(
            "dev_email_not_sent_no_smtp_configured",
            to=to,
            subject=subject,
            body=body,
        )
        return

    message = EmailMessage()
    message["From"] = settings.smtp_from_address
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        if settings.smtp_username and settings.smtp_password:
            smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)


def send_password_reset_email(to: str, token: str) -> None:
    settings = get_settings()
    link = f"{settings.frontend_base_url}/reset-password?token={token}"
    send_email(
        to=to,
        subject="Reset your StromeX password",
        body=(
            "Someone requested a password reset for this StromeX account.\n\n"
            f"Reset it here (valid for 1 hour): {link}\n\n"
            "If you didn't request this, you can ignore this email."
        ),
    )


def send_email_verification_email(to: str, token: str) -> None:
    settings = get_settings()
    link = f"{settings.frontend_base_url}/verify-email?token={token}"
    send_email(
        to=to,
        subject="Verify your StromeX email address",
        body=(
            "Confirm this email address for your StromeX account.\n\n"
            f"Verify it here (valid for 24 hours): {link}"
        ),
    )
