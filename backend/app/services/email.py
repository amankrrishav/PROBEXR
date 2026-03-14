import smtplib
from email.message import EmailMessage
import asyncio
import logging

from app.config import get_config

logger = logging.getLogger(__name__)

async def send_magic_link_email(to_email: str, magic_link: str) -> None:
    """Send a magic link via SMTP. Falls back to console log if no SMTP_HOST is configured."""
    cfg = get_config()
    
    # If no SMTP host is configured, fallback to console (useful for development)
    if not cfg.smtp_host:
        logger.info(f"MAGIC LINK for {to_email}: {magic_link}")
        print(f"\n[DEVELOPMENT] MAGIC LINK for {to_email}: {magic_link}\n")
        return

    msg = EmailMessage()
    msg["Subject"] = "Your PROBEXR Login Link"
    msg["From"] = cfg.smtp_from_email
    msg["To"] = to_email
    
    msg.set_content(f"""
Hi there,

Here is your login link for PROBEXR:
{magic_link}

If you didn't request this, you can safely ignore this email.

Thanks,
The PROBEXR Team
    """)
    
    msg.add_alternative(f"""
    <html>
      <body>
        <p>Hi there,</p>
        <p>Click the button below to log in to PROBEXR:</p>
        <a href="{magic_link}" style="display:inline-block;padding:10px 20px;background-color:#000;color:#fff;text-decoration:none;border-radius:5px;font-weight:bold;">Log in to PROBEXR</a>
        <p>Or copy and paste this link into your browser:<br><a href="{magic_link}">{magic_link}</a></p>
        <p>If you didn't request this, you can safely ignore this email.</p>
        <p>Thanks,<br>The PROBEXR Team</p>
      </body>
    </html>
    """, subtype="html")

    def _send_email():
        try:
            with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port) as server:
                server.starttls()
                if cfg.smtp_user and cfg.smtp_password:
                    server.login(cfg.smtp_user, cfg.smtp_password)
                server.send_message(msg)
                logger.info(f"Magic link email sent successfully to {to_email}")
        except Exception as e:
            logger.error(f"SMTP error while sending email to {to_email}: {str(e)}")
            raise
            
    try:
        await asyncio.to_thread(_send_email)
    except Exception as e:
        raise ValueError(f"Failed to send email: {str(e)}")
