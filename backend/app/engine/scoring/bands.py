from typing import Dict, Any, Tuple


def get_risk_band(score: int, is_critical: bool = False, is_unusable: bool = False) -> Tuple[str, str]:
    """
    Returns (risk_level, label) based on ARCHITECTURE Section 8.5.
    0–24: likely_safe
    25–44: suspicious
    45–64: medium
    65–100: high
    critical: only if score >= 85 AND (threat intel hit or credential/payment + impersonation)
    unable_to_verify: input is empty or unusable.
    """
    if is_unusable:
        return "unable_to_verify", "Unable to Verify"

    if is_critical and score >= 85:
        return "critical", "Critical Threat"

    if score >= 65:
        return "high", "High Risk"
    elif score >= 45:
        return "medium", "Medium Risk"
    elif score >= 25:
        return "suspicious", "Suspicious"
    else:
        return "likely_safe", "Likely Safe"


def determine_category(indicators: list, risk_level: str) -> Dict[str, str]:
    """Determines category code and label based on detected risk indicators."""
    if risk_level in ("likely_safe", "unable_to_verify") and not indicators:
        if risk_level == "unable_to_verify":
            return {"code": "unverifiable", "label": "Unverifiable Content"}
        return {"code": "legitimate_communication", "label": "Likely Legitimate Communication"}

    codes = {ind.code for ind in indicators}

    if "GOV_IMPERSONATION_DIGITAL_ARREST" in codes:
        return {"code": "digital_arrest_scam", "label": "Law Enforcement / Digital Arrest Scam"}
    if "FAMILY_EMERGENCY_IMPERSONATION" in codes:
        return {"code": "family_emergency_scam", "label": "Family Emergency Impersonation Scam"}
    if "CRED_PIN_REQUEST" in codes or "UPI_RECEIVE_PIN_SCAM" in codes:
        return {"code": "upi_pin_fraud", "label": "UPI PIN / Collect Request Scam"}
    if "QR_PAY_REWARD_TRAP" in codes:
        return {"code": "qr_reward_scam", "label": "Potential QR / Reward Scam"}
    if "FIN_INVESTMENT_GUARANTEE" in codes:
        return {"code": "investment_fraud", "label": "Unregulated Investment / Stock Tips Scheme"}
    if "JOB_TASK_FRAUD" in codes:
        return {"code": "fake_job_fraud", "label": "Part-Time Job / Task Fraud"}
    if "FIN_INSTANT_LOAN_UPFRONT" in codes:
        return {"code": "loan_advance_fee", "label": "Instant Loan / Advance Fee Scam"}
    if "FIN_LOTTERY_ADVANCE_FEE" in codes:
        return {"code": "lottery_scam", "label": "Lottery / Lucky Draw Fee Fraud"}
    if "FIN_TAX_REFUND_PHISH" in codes:
        return {"code": "tax_refund_phishing", "label": "Tax Refund Phishing Scam"}
    if "ACC_SUSPENSION_THREAT" in codes or "KYC_COERCION" in codes:
        return {"code": "kyc_suspension_phishing", "label": "KYC / Account Suspension Threat"}
    if "CRED_OTP_REQUEST" in codes:
        return {"code": "otp_theft", "label": "OTP Solicitation / Account Takeover"}
    if "DECEPTIVE_URL_DETECTED" in codes:
        return {"code": "phishing_link", "label": "Deceptive / Phishing Website"}
    if "URL_SHORTENER_DETECTED" in codes:
        return {"code": "unverified_link", "label": "Unverified Link Destination"}

    return {"code": "suspicious_communication", "label": "Suspicious Communication"}
