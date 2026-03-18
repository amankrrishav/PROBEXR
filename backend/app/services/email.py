import smtplib
from email.message import EmailMessage
import asyncio
import logging

from app.config import get_config

logger = logging.getLogger(__name__)

async def send_account_exists_email(to_email: str, login_link: str) -> None:
    """
    Notify an existing user that someone tried to register with their email.
    Provides a magic-link so they can log back in without a password.
    Falls back to console log if no SMTP_HOST configured.
    """
    cfg = get_config()

    if not cfg.smtp_host:
        logger.info("Account-exists email queued for %s", to_email)
        logger.debug("[DEV] Account-exists email for %s: %s", to_email, login_link)
        return

    msg = EmailMessage()
    msg["Subject"] = "Someone tried to sign up with your PROBEXR email"
    msg["From"] = cfg.smtp_from_email
    msg["To"] = to_email

    msg.set_content(f"""
Hi there,

Someone just tried to create a PROBEXR account using your email address.

If that was you and you already have an account, click the link below to log in:
{login_link}

If that wasn't you, you can safely ignore this email — no changes were made to your account.

Thanks,
The PROBEXR Team
    """)

    msg.add_alternative(f"""
    <html>
      <body>
        <p>Hi there,</p>
        <p>Someone just tried to create a PROBEXR account using your email address.</p>
        <p>If that was you and you already have an account, click below to log in:</p>
        <a href="{login_link}" style="display:inline-block;padding:10px 20px;background-color:#000;color:#fff;text-decoration:none;border-radius:5px;font-weight:bold;">Log in to PROBEXR</a>
        <p>If that wasn't you, you can safely ignore this email — no changes were made.</p>
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
                logger.info("Account-exists email sent to %s", to_email)
        except Exception as e:
            logger.error("SMTP error sending account-exists email to %s: %s", to_email, e)
            raise

    try:
        await asyncio.to_thread(_send_email)
    except Exception as e:
        raise ValueError(f"Failed to send email: {str(e)}")


async def send_verification_email(to_email: str, verification_link: str) -> None:
    """Send email verification link. Falls back to console log if no SMTP_HOST configured."""
    cfg = get_config()

    if not cfg.smtp_host:
        logger.info("Verification email queued for %s", to_email)
        logger.debug("[DEV] Verification link for %s: %s", to_email, verification_link)
        return

    msg = EmailMessage()
    msg["Subject"] = "Verify your PROBEXR email address"
    msg["From"] = cfg.smtp_from_email
    msg["To"] = to_email

    msg.set_content(f"""
Hi there,

Thanks for signing up for PROBEXR! Please verify your email address by clicking the link below (expires in 24 hours):
{verification_link}

If you didn't create an account, you can safely ignore this email.

Thanks,
The PROBEXR Team
    """)

    msg.add_alternative(f"""
    <html>
      <body>
        <p>Hi there,</p>
        <p>Thanks for signing up for PROBEXR! Please verify your email address:</p>
        <a href="{verification_link}" style="display:inline-block;padding:10px 20px;background-color:#000;color:#fff;text-decoration:none;border-radius:5px;font-weight:bold;">Verify Email</a>
        <p>Or copy and paste this link:<br><a href="{verification_link}">{verification_link}</a></p>
        <p><strong>This link expires in 24 hours.</strong></p>
        <p>If you didn't create an account, you can safely ignore this email.</p>
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
                logger.info("Verification email sent to %s", to_email)
        except Exception as e:
            logger.error("SMTP error sending verification email to %s: %s", to_email, e)
            raise

    try:
        await asyncio.to_thread(_send_email)
    except Exception as e:
        raise ValueError(f"Failed to send email: {str(e)}")


async def send_password_reset_email(to_email: str, reset_link: str) -> None:
    """Send a password reset email. Falls back to console log if no SMTP_HOST configured."""
    cfg = get_config()

    if not cfg.smtp_host:
        logger.info("Password reset email queued for %s", to_email)
        logger.debug("[DEV] Password reset link for %s: %s", to_email, reset_link)
        return

    msg = EmailMessage()
    msg["Subject"] = "Reset your PROBEXR password"
    msg["From"] = cfg.smtp_from_email
    msg["To"] = to_email

    msg.set_content(f"""
Hi there,

We received a request to reset your PROBEXR password.

Click the link below to set a new password (expires in 30 minutes):
{reset_link}

If you didn't request a password reset, you can safely ignore this email.
Your password will not be changed.

Thanks,
The PROBEXR Team
    """)

    msg.add_alternative(f"""
    <html>
      <body>
        <p>Hi there,</p>
        <p>We received a request to reset your PROBEXR password.</p>
        <a href="{reset_link}" style="display:inline-block;padding:10px 20px;background-color:#000;color:#fff;text-decoration:none;border-radius:5px;font-weight:bold;">Reset Password</a>
        <p>Or copy and paste this link:<br><a href="{reset_link}">{reset_link}</a></p>
        <p><strong>This link expires in 30 minutes.</strong></p>
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
                logger.info("Password reset email sent to %s", to_email)
        except Exception as e:
            logger.error("SMTP error sending password reset email to %s: %s", to_email, e)
            raise

    try:
        await asyncio.to_thread(_send_email)
    except Exception as e:
        raise ValueError(f"Failed to send email: {str(e)}")


async def send_magic_link_email(to_email: str, magic_link: str) -> None:
    """Send a magic link via SMTP. Falls back to console log if no SMTP_HOST is configured."""
    cfg = get_config()
    
    # If no SMTP host is configured, fallback to console (useful for development)
    if not cfg.smtp_host:
        logger.info("Magic link email queued for %s", to_email)
        logger.debug("[DEV] Magic link for %s: %s", to_email, magic_link)
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
                logger.info("Magic link email sent to %s", to_email)
        except Exception as e:
            logger.error("SMTP error sending magic link email to %s: %s", to_email, e)
            raise
            
    try:
        await asyncio.to_thread(_send_email)
    except Exception as e:
        raise ValueError(f"Failed to send email: {str(e)}")