import io
import json
import urllib.error
import urllib.request
from unittest.mock import MagicMock

import pytest
from app.core.config import settings
from app.services import email_service
from app.services.email_service import send_verification_email as real_send_verification_email


@pytest.fixture(autouse=True)
def override_conftest_fixtures(monkeypatch):
    """
    Ensure we are testing the actual send_verification_email function
    rather than the global mock_email_sender fixture from conftest.py.
    """
    monkeypatch.setattr("app.services.email_service.send_verification_email", real_send_verification_email)
    yield


@pytest.fixture(autouse=True)
def clean_test_tables():
    """No database tables needed for Brevo unit tests."""
    yield


@pytest.fixture(scope="session", autouse=True)
def verify_test_database():
    """No database connection needed for Brevo unit tests."""
    yield


def test_brevo_email_url_headers_and_payload(monkeypatch):
    """
    Checks:
    - correct URL: https://api.brevo.com/v3/smtp/email
    - api-key header: matches BREVO_API_KEY
    - sender/to JSON: parsed sender name & email from EMAIL_FROM, recipient in 'to'
    """
    test_key = "xkeysib-test-fake-api-key-12345"
    test_from = "GARUDA <garudaadmin26@gmail.com>"
    recipient = "user@example.com"
    code = "654321"

    monkeypatch.setattr(settings, "BREVO_API_KEY", test_key)
    monkeypatch.setattr(settings, "EMAIL_FROM", test_from)

    captured_request = None

    def fake_urlopen(req, timeout=15):
        nonlocal captured_request
        captured_request = req
        assert timeout == 15
        mock_resp = MagicMock()
        mock_resp.status = 201
        mock_resp.read.return_value = b'{"messageId":"<test-msg-id@brevo>"}'
        mock_resp.__enter__.return_value = mock_resp
        return mock_resp

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    result = email_service.send_verification_email(recipient, code)
    assert result is True
    assert captured_request is not None

    # 1. Correct URL
    assert captured_request.full_url == "https://api.brevo.com/v3/smtp/email"
    assert captured_request.get_method() == "POST"

    # 2. API-Key Header and content headers
    assert captured_request.get_header("Api-key") == test_key
    assert captured_request.get_header("Content-type") == "application/json"
    assert captured_request.get_header("Accept") == "application/json"

    # 3. Sender/to JSON body
    body = json.loads(captured_request.data.decode("utf-8"))
    assert body["sender"] == {"name": "GARUDA", "email": "garudaadmin26@gmail.com"}
    assert body["to"] == [{"email": recipient}]
    assert body["subject"] == "GARUDA Verification Code"
    assert code in body["textContent"]
    assert "Your GARUDA verification code is 654321." in body["textContent"]


def test_brevo_email_400_response_raises_runtime_error(monkeypatch):
    """
    Checks that an HTTP 400 error from Brevo API raises RuntimeError
    with message matching 'Brevo API delivery failed: 400 ...'
    """
    test_key = "xkeysib-test-fake-api-key-12345"
    monkeypatch.setattr(settings, "BREVO_API_KEY", test_key)
    monkeypatch.setattr(settings, "EMAIL_FROM", "GARUDA <garudaadmin26@gmail.com>")

    error_body = b'{"code":"invalid_parameter","message":"invalid recipient"}'

    def fake_urlopen_400(req, timeout=15):
        raise urllib.error.HTTPError(
            url="https://api.brevo.com/v3/smtp/email",
            code=400,
            msg="Bad Request",
            hdrs={},
            fp=io.BytesIO(error_body),
        )

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen_400)

    with pytest.raises(RuntimeError) as exc_info:
        email_service.send_verification_email("bad-email", "112233")

    msg = str(exc_info.value)
    assert "Brevo API delivery failed: 400" in msg
    assert "invalid recipient" in msg


def test_brevo_email_non_2xx_status_raises_runtime_error(monkeypatch):
    """
    Checks that a non-2xx status code returned without an exception raises RuntimeError.
    """
    monkeypatch.setattr(settings, "BREVO_API_KEY", "xkeysib-fake-key")
    monkeypatch.setattr(settings, "EMAIL_FROM", "GARUDA <garudaadmin26@gmail.com>")

    def fake_urlopen_500(req, timeout=15):
        mock_resp = MagicMock()
        mock_resp.status = 500
        mock_resp.read.return_value = b'{"message":"internal server error"}'
        mock_resp.__enter__.return_value = mock_resp
        return mock_resp

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen_500)

    with pytest.raises(RuntimeError) as exc_info:
        email_service.send_verification_email("user@example.com", "123456")

    assert "Brevo API delivery failed: 500" in str(exc_info.value)


def test_brevo_api_key_never_leaked_in_exceptions(monkeypatch):
    """
    Ensures the BREVO_API_KEY is redacted and never leaked in exceptions or errors.
    """
    secret_key = "super-secret-brevo-key-999"
    monkeypatch.setattr(settings, "BREVO_API_KEY", secret_key)
    monkeypatch.setattr(settings, "EMAIL_FROM", "GARUDA <garudaadmin26@gmail.com>")

    def fake_urlopen_leak(req, timeout=15):
        raise urllib.error.HTTPError(
            url="https://api.brevo.com/v3/smtp/email",
            code=401,
            msg="Unauthorized",
            hdrs={},
            fp=io.BytesIO(f"Error with key {secret_key}".encode("utf-8")),
        )

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen_leak)

    with pytest.raises(RuntimeError) as exc_info:
        email_service.send_verification_email("user@example.com", "123456")

    err_str = str(exc_info.value)
    assert secret_key not in err_str
    assert "[REDACTED]" in err_str


def test_brevo_counts_as_configured_in_production(monkeypatch):
    """
    The 'not configured in production' check must count BREVO_API_KEY as configured.
    When APP_ENV=production and BREVO_API_KEY is set, it does NOT raise
    'Email delivery is not configured in production'.
    """
    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "BREVO_API_KEY", "xkeysib-prod-key")
    monkeypatch.setattr(settings, "SMTP_USER", "")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "")

    called = False

    def fake_urlopen(req, timeout=15):
        nonlocal called
        called = True
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b'{}'
        mock_resp.__enter__.return_value = mock_resp
        return mock_resp

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    res = email_service.send_verification_email("prod-user@example.com", "999888")
    assert res is True
    assert called is True


def test_production_without_brevo_and_without_smtp_raises(monkeypatch):
    """
    When in production and neither Brevo nor SMTP is configured,
    raises RuntimeError('Email delivery is not configured in production.').
    """
    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "BREVO_API_KEY", None)
    monkeypatch.setattr(settings, "SMTP_USER", "")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "")

    with pytest.raises(RuntimeError) as exc_info:
        email_service.send_verification_email("prod-user@example.com", "999888")

    assert "Email delivery is not configured in production." in str(exc_info.value)


def test_development_without_config_prints_to_console(monkeypatch, capsys):
    """
    When in development and neither is configured, prints code to console and returns True.
    """
    monkeypatch.setattr(settings, "APP_ENV", "development")
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "BREVO_API_KEY", None)
    monkeypatch.setattr(settings, "SMTP_USER", "")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "")

    res = email_service.send_verification_email("dev@example.com", "123789")
    assert res is True
    captured = capsys.readouterr()
    assert "[DEV CONSOLE EMAIL] Your GARUDA verification code for dev@example.com is: 123789" in captured.out


@pytest.mark.parametrize(
    "email_from,expected_sender",
    [
        (
            "GARUDA <garudaadmin26@gmail.com>",
            {"name": "GARUDA", "email": "garudaadmin26@gmail.com"},
        ),
        (
            "Security Team <alert@garuda.app>",
            {"name": "Security Team", "email": "alert@garuda.app"},
        ),
        (
            "admin@garuda.app",
            {"name": "GARUDA", "email": "admin@garuda.app"},
        ),
    ],
)
def test_brevo_sender_parsing_parseaddr(monkeypatch, email_from, expected_sender):
    """
    Checks that EMAIL_FROM is parsed correctly using email.utils.parseaddr.
    """
    monkeypatch.setattr(settings, "BREVO_API_KEY", "xkeysib-test-key")
    monkeypatch.setattr(settings, "EMAIL_FROM", email_from)

    captured_payload = None

    def fake_urlopen(req, timeout=15):
        nonlocal captured_payload
        captured_payload = json.loads(req.data.decode("utf-8"))
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b'{}'
        mock_resp.__enter__.return_value = mock_resp
        return mock_resp

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    res = email_service.send_verification_email("user@example.com", "123456")
    assert res is True
    assert captured_payload is not None
    assert captured_payload["sender"] == expected_sender


def test_smtp_fallback_when_brevo_key_not_set(monkeypatch):
    """
    If BREVO_API_KEY is not set, keep the existing SMTP code exactly as it is.
    """
    monkeypatch.setattr(settings, "BREVO_API_KEY", None)
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.test.com")
    monkeypatch.setattr(settings, "SMTP_PORT", 587)
    monkeypatch.setattr(settings, "SMTP_USER", "smtp_user@test.com")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "smtp_secret_pass")
    monkeypatch.setattr(settings, "EMAIL_FROM", "GARUDA <garudaadmin26@gmail.com>")

    urlopen_called = False

    def fake_urlopen(req, timeout=15):
        nonlocal urlopen_called
        urlopen_called = True
        raise AssertionError("urlopen should NOT be called when BREVO_API_KEY is not set")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    mock_smtp_instance = MagicMock()
    mock_smtp_class = MagicMock(return_value=mock_smtp_instance)
    mock_smtp_instance.__enter__.return_value = mock_smtp_instance

    monkeypatch.setattr("smtplib.SMTP", mock_smtp_class)

    res = email_service.send_verification_email("user@example.com", "555666")
    assert res is True
    assert urlopen_called is False
    assert mock_smtp_class.called
    assert mock_smtp_instance.starttls.called
    assert mock_smtp_instance.login.called
    assert mock_smtp_instance.send_message.called

