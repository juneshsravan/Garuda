import os
import sys
from pathlib import Path
from email.mime.text import MIMEText
import smtplib

# Add backend directory to sys.path so app imports work
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.config import settings


def test_smtp_delivery():
    print("==================================================")
    print("      GARUDA SMTP CONFIGURATION & TEST RUNNER     ")
    print("==================================================")
    print(f"Working Directory : {os.getcwd()}")
    print(f"APP_ENV           : {settings.APP_ENV}")
    print(f"ENVIRONMENT       : {settings.ENVIRONMENT}")
    print(f"is_development    : {settings.is_development}")
    print("--------------------------------------------------")
    print("Settings loaded from backend/.env:")
    print(f"  SMTP_HOST         : {settings.SMTP_HOST}")
    print(f"  SMTP_PORT         : {settings.SMTP_PORT}")
    print(f"  SMTP_USER         : {settings.SMTP_USER}")
    print(f"  EMAIL_FROM        : {settings.EMAIL_FROM}")
    
    app_pwd = (settings.SMTP_APP_PASSWORD or "").strip()
    pwd = (settings.SMTP_PASSWORD or "").strip()
    effective_pwd = settings.effective_smtp_password.replace(" ", "").strip()
    
    print(f"  SMTP_APP_PASSWORD : {'[Configured]' if app_pwd else '[Missing]'} (length: {len(app_pwd)})")
    print(f"  SMTP_PASSWORD     : {'[Configured]' if pwd else '[Missing]'} (length: {len(pwd)})")
    print(f"  Active password   : {'[Present]' if effective_pwd else '[Missing]'} (length: {len(effective_pwd)})")
    print("==================================================")

    if not settings.SMTP_HOST or not settings.SMTP_USER or not effective_pwd:
        print("[ERROR] Missing required SMTP configuration in backend/.env.")
        print("Please ensure SMTP_HOST, SMTP_PORT, SMTP_USER, and SMTP_APP_PASSWORD are set.")
        sys.exit(1)

    host = settings.SMTP_HOST
    port = int(settings.SMTP_PORT) if settings.SMTP_PORT else 587
    user = settings.SMTP_USER.strip()
    sender = settings.EMAIL_FROM.strip() if settings.EMAIL_FROM else user
    recipient = user

    print(f"Connecting to {host}:{port} via smtplib.SMTP...")
    
    msg = MIMEText(
        "This is an automated test email from GARUDA.\n"
        "If you are reading this in your inbox, your SMTP configuration is 100% operational.",
        "plain",
        "utf-8",
    )
    msg["Subject"] = "GARUDA SMTP Test Verification"
    msg["From"] = sender
    msg["To"] = recipient

    server = None
    try:
        # Step 1: Connect
        server = smtplib.SMTP(host, port, timeout=20)
        print("-> [1/4] Connected to SMTP server.")

        # Step 2: EHLO & STARTTLS
        server.ehlo()
        print("-> [2/4] Negotiating TLS encryption (STARTTLS)...")
        server.starttls()
        server.ehlo()

        # Step 3: Login
        print(f"-> [3/4] Authenticating as {user} with app password...")
        server.login(user, effective_pwd)
        print("-> Authentication successful!")

        # Step 4: Send message
        print(f"-> [4/4] Sending test message to {recipient}...")
        server.send_message(msg)
        print(f"\n[SUCCESS] Test email successfully sent to {recipient}!")
        print("Check your Gmail inbox and Sent folder.")
    except Exception as exc:
        err_type = type(exc).__name__
        err_msg = str(exc).strip()
        # Ensure password is never printed under any circumstances
        if effective_pwd and effective_pwd in err_msg:
            err_msg = err_msg.replace(effective_pwd, "[REDACTED]")
        if app_pwd and app_pwd in err_msg:
            err_msg = err_msg.replace(app_pwd, "[REDACTED]")
        if pwd and pwd in err_msg:
            err_msg = err_msg.replace(pwd, "[REDACTED]")

        print("\n--------------------------------------------------")
        print("[FAILED] SMTP Test Delivery Failed!")
        print(f"Exception Type    : {err_type}")
        print(f"Exception Message : {err_msg}")
        print("--------------------------------------------------")
        
        # Diagnostic advice for common Gmail SMTP errors
        if "535" in err_msg or "BadCredentials" in err_msg or "SMTPServerDisconnected" in err_type:
            print("\nDIAGNOSTIC ANALYSIS:")
            print("Google SMTP rejected the credentials (535 5.7.8 BadCredentials).")
            print("Root cause:")
            print("1. 'SMTP_APP_PASSWORD' in backend/.env is currently a standard password (e.g. 9 chars),")
            print("   or an invalid/revoked app password.")
            print("2. Google SMTP strictly requires a 16-character 'App Password' generated at:")
            print("   https://myaccount.google.com/apppasswords")
            print("   (Google Account -> Security -> 2-Step Verification -> App passwords).")
            print("3. Standard Gmail passwords are NOT accepted by smtp.gmail.com since May 2022.")
        sys.exit(1)
    finally:
        if server:
            try:
                server.quit()
            except Exception:
                pass


if __name__ == "__main__":
    test_smtp_delivery()
