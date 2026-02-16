"""
Email service - sends emails via SMTP (MailHog in development).
"""

import logging
from email.message import EmailMessage
from pathlib import Path

import aiosmtplib
from jinja2 import Environment, FileSystemLoader

from app.config.settings import settings

logger = logging.getLogger(__name__)

# Load templates from app/templates/
templates_dir = Path(__file__).parent.parent / "templates"
jinja_env = Environment(loader=FileSystemLoader(str(templates_dir)))


async def send_email(to: str, subject: str, template_name: str, context: dict) -> dict:
    """Render a Jinja2 template and send it via SMTP to MailHog.

    Returns dict with "status" ("sent" or "failed") and optional "error_message".
    """
    try:
        template = jinja_env.get_template(template_name)
        html_body = template.render(**context)

        message = EmailMessage()
        message["From"] = settings.smtp_from
        message["To"] = to
        message["Subject"] = subject
        message.set_content(subject)  # plain-text fallback
        message.add_alternative(html_body, subtype="html")

        await aiosmtplib.send(
            message,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            use_tls=False,
        )

        logger.info("Email sent to %s: %s", to, subject)
        return {"status": "sent"}

    except Exception as e:
        logger.error("Failed to send email to %s: %s", to, e)
        return {"status": "failed", "error_message": str(e)}
