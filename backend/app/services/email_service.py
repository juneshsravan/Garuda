import json
import logging
import smtplib
import urllib.error
import urllib.request
from email.mime.text import MIMEText
from email.utils import parseaddr

from app.core.config import settings

logger = logging.getLogger("garuda.email")


def send_verification_email(to_email: str, code: str) -> bool:
    """
    Sends a 6-digit verification code using Brevo HTTP API or Gmail SMTP.
    - If BREVO_API_KEY is configured, sends via Brevo's HTTPS API (works on Render free).
    - Otherwise, falls back to SMTP if SMTP credentials are configured.
    - If neither is configured in development, logs the code to the console.
    - If neither is configured in production, raises RuntimeError.
    """
    raw_password = settings.effective_smtp_password
    password = raw_password.replace(" ", "").strip() if raw_password else ""
    
    smtp_host = settings.SMTP_HOST.strip() if settings.SMTP_HOST else "smtp.gmail.com"
    smtp_port = int(settings.SMTP_PORT) if settings.SMTP_PORT else 587
    smtp_user = settings.SMTP_USER.strip() if settings.SMTP_USER else ""
    email_from = settings.EMAIL_FROM.strip() if settings.EMAIL_FROM else smtp_user

    is_brevo_configured = bool(settings.BREVO_API_KEY and settings.BREVO_API_KEY.strip())
    is_smtp_configured = bool(
        smtp_host
        and smtp_port
        and smtp_user
        and password
    )
    is_configured = is_brevo_configured or is_smtp_configured

    if not is_configured:
        if settings.is_development:
            print(f"[DEV CONSOLE EMAIL] Your GARUDA verification code for {to_email} is: {code}")
            logger.info("SMTP variables missing in development mode; verification code logged to console.")
            return True
        else:
            logger.error("SMTP environment variables are missing in production. Cannot send verification email.")
            raise RuntimeError("Email delivery is not configured in production.")

    email_body = f"Your GARUDA verification code is {code}. It expires in 10 minutes. Never share this code."

    if is_brevo_configured:
        sender_name, sender_email = parseaddr(email_from)
        if not sender_email:
            sender_email = email_from or smtp_user or "garudaadmin26@gmail.com"
        if not sender_name:
            sender_name = "GARUDA"

        payload = {
            "sender": {"name": sender_name, "email": sender_email},
            "to": [{"email": to_email}],
            "subject": "GARUDA Verification Code",
            "textContent": email_body,
        }

        req = urllib.request.Request(
            "https://api.brevo.com/v3/smtp/email",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "api-key": settings.BREVO_API_KEY,
                "Content-Type": "application/json",
                "accept": "application/json",
            },
            method="POST",
        )

        brevo_key = settings.BREVO_API_KEY or ""
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                status_code = getattr(response, "status", None) or response.getcode()
                if not (200 <= status_code < 300):
                    raw_resp = response.read().decode("utf-8", errors="replace").strip()
                    short_text = raw_resp[:200] if raw_resp else str(status_code)
                    if brevo_key and brevo_key in short_text:
                        short_text = short_text.replace(brevo_key, "[REDACTED]")
                    logger.error(f"Failed to send email via Brevo API to {to_email}: status {status_code}")
                    raise RuntimeError(f"Brevo API delivery failed: {status_code} {short_text}")
                logger.info(f"Successfully sent verification email to {to_email} via Brevo")
                return True
        except urllib.error.HTTPError as exc:
            status_code = exc.code
            try:
                raw_resp = exc.read().decode("utf-8", errors="replace").strip()
            except Exception:
                raw_resp = str(exc.reason)
            short_text = raw_resp[:200] if raw_resp else str(exc.reason)
            if brevo_key and brevo_key in short_text:
                short_text = short_text.replace(brevo_key, "[REDACTED]")
            logger.error(f"Failed to send email via Brevo API to {to_email}: status {status_code}")
            raise RuntimeError(f"Brevo API delivery failed: {status_code} {short_text}") from None
        except RuntimeError:
            raise
        except Exception as exc:
            err_msg = str(exc).strip()
            if brevo_key and brevo_key in err_msg:
                err_msg = err_msg.replace(brevo_key, "[REDACTED]")
            logger.error(f"Failed to send email via Brevo API to {to_email}: {type(exc).__name__}: {err_msg}")
            raise RuntimeError(f"Brevo API delivery failed: {type(exc).__name__}: {err_msg}") from None

    # SMTP fallback / default when BREVO_API_KEY is not set
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
