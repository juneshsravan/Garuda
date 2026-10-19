import logging
import smtplib
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger("garuda.email")


def send_verification_email(to_email: str, code: str) -> bool:
    """
    Sends a 6-digit verification code using Gmail SMTP.
    Uses smtplib.SMTP(host, 587) + starttls() + login(user, app_password) + send_message.
    Logs the exception type and message on failure (never the password).
    
    If SMTP env vars are missing AND ENVIRONMENT/APP_ENV is development,
    logs the code to the console instead of sending (never in production).
    """
    raw_password = settings.effective_smtp_password
    password = raw_password.replace(" ", "").strip() if raw_password else ""
    
    smtp_host = settings.SMTP_HOST.strip() if settings.SMTP_HOST else "smtp.gmail.com"
    smtp_port = int(settings.SMTP_PORT) if settings.SMTP_PORT else 587
    smtp_user = settings.SMTP_USER.strip() if settings.SMTP_USER else ""
    email_from = settings.EMAIL_FROM.strip() if settings.EMAIL_FROM else smtp_user

    is_smtp_configured = bool(
        smtp_host
        and smtp_port
        and smtp_user
        and password
    )

    if not is_smtp_configured:
        if settings.is_development:
            print(f"[DEV CONSOLE EMAIL] Your GARUDA verification code for {to_email} is: {code}")
            logger.info("SMTP variables missing in development mode; verification code logged to console.")
            return True
        else:
            logger.error("SMTP environment variables are missing in production. Cannot send verification email.")
            raise RuntimeError("Email delivery is not configured in production.")

    email_body = f"Your GARUDA verification code is {code}. It expires in 10 minutes. Never share this code."
    msg = MIMEText(email_body, "plain", "utf-8")
    msg["Subject"] = "GARUDA Verification Code"
    msg["From"] = email_from
    msg["To"] = to_email

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(smtp_user, password)
            server.send_message(msg)
        logger.info(f"Successfully sent verification email to {to_email}")
        return True
    except Exception as exc:
        err_msg = str(exc).strip()
        if password and password in err_msg:
            err_msg = err_msg.replace(password, "[REDACTED]")
        if raw_password and raw_password in err_msg:
            err_msg = err_msg.replace(raw_password, "[REDACTED]")
        logger.error(
            f"Failed to send email via SMTP to {to_email}: {type(exc).__name__}: {err_msg}"
        )
        raise RuntimeError(f"SMTP delivery failed: {type(exc).__name__}: {err_msg}") from None
