import logging
import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_verification_email(to_email: str, code: str, purpose: str) -> None:
    """Send a one-time code; production refuses to silently skip SMTP delivery."""
    if not settings.smtp_host:
        if settings.app_env.lower() == "production":
            raise RuntimeError("SMTP_HOST must be configured in production")
        logger.warning(
            "AutoFlow development email code: recipient=%s purpose=%s code=%s",
            to_email,
            purpose,
            code,
        )
        return

    sender = settings.smtp_from_email or settings.smtp_username
    if not sender:
        raise RuntimeError("Set SMTP_FROM_EMAIL or SMTP_USERNAME to a verified sender address")

    message = EmailMessage()
    message["Subject"] = "Код подтверждения AutoFlow"
    message["From"] = sender
    message["To"] = to_email
    message.set_content(
        "Здравствуйте!\n\n"
        f"Ваш код подтверждения AutoFlow: {code}\n"
        "Код действует 10 минут. Никому не сообщайте его. "
        "Если вы не запрашивали код, просто проигнорируйте письмо.\n\n"
        "Команда AutoFlow"
    )
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
        if settings.smtp_use_tls:
            server.starttls(context=ssl.create_default_context())
        if settings.smtp_username:
            server.login(settings.smtp_username, settings.smtp_password or "")
        server.send_message(message)
