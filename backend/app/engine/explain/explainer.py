from typing import List, Dict, Any
from app.engine.analyzers.text_rules import Indicator
from app.engine.analyzers.legitimacy import LegitimacySignal


def build_explanation(
    indicators: List[Indicator],
    legitimacy_signals: List[LegitimacySignal],
    risk_level: str,
    urls: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Builds context-specific summary, recommendations, and safe verification steps
    strictly derived from detected signals in THIS input (ARCHITECTURE Rule 7 & 10).
    """
    if risk_level == "unable_to_verify":
        return {
            "summary": "The input contains insufficient text, symbols, or uninterpretable characters to perform verification.",
            "recommendations": [
                "Provide the complete original message text if you suspect it is malicious.",
            ],
            "verify_steps": [
                "Check the sender's identity through known official communication channels.",
            ],
        }

    if risk_level == "likely_safe":
        if legitimacy_signals:
            signal_labels = [s.label.lower() for s in legitimacy_signals]
            summary = f"Likely Safe: The message exhibits standard authentic patterns ({', '.join(signal_labels)})."
        else:
            summary = "Likely Safe: No indicators of scam, credential solicitation, or coercive urgency were detected in this text."

        return {
            "summary": summary,
            "recommendations": [
                "Continue standard vigilance: verify account details directly inside your banking or provider app.",
            ],
            "verify_steps": [
                "Always check transaction details against official bank statements or provider dashboards.",
            ],
        }

    # Threat / Suspicious explanations built dynamically
    threat_reasons = []
    recommendations = []
    verify_steps = []

    codes = {ind.code for ind in indicators}

    if "CRED_OTP_REQUEST" in codes:
        threat_reasons.append("soliciting your one-time password (OTP)")
        recommendations.append("Do NOT share your OTP or SMS verification codes with anyone under any circumstances.")
        verify_steps.append("Remember that banks, payment gateways, and government agencies never call or message to ask for OTPs.")

    if "CRED_PIN_REQUEST" in codes:
        threat_reasons.append("demanding that you approve a UPI request or enter your PIN to receive funds")
        recommendations.append("Do NOT enter your UPI PIN. Entering your UPI PIN always deducts money from your account.")
        verify_steps.append("Receiving money via UPI never requires entering a PIN or approving a collect request.")

    if "QR_PAY_REWARD_TRAP" in codes:
        threat_reasons.append("instructing you to scan a QR code to claim rewards or cashback")
        recommendations.append("Do NOT scan the QR code. In UPI architecture, scanning a QR code is strictly for paying, never for receiving.")
        verify_steps.append("Legitimate cashback is credited automatically to your linked account or wallet.")

    if "ACC_SUSPENSION_THREAT" in codes or "KYC_COERCION" in codes:
        threat_reasons.append("threatening immediate account suspension or service disconnection unless KYC/PAN is updated")
        recommendations.append("Do not call phone numbers or tap links provided in suspension notices.")
        verify_steps.append("Log in to your bank or provider's official mobile application independently to verify your KYC status.")

    if "GOV_IMPERSONATION_DIGITAL_ARREST" in codes:
        threat_reasons.append("impersonating customs or law enforcement officers with threats of illegal parcels and digital arrest")
        recommendations.append("Immediately disconnect and report the contact. Official law enforcement never conducts interrogations or arrests over video calls.")
        verify_steps.append("Report suspected cybercrime impersonation immediately to cybercrime.gov.in or the national helpline 1930.")

    if "JOB_TASK_FRAUD" in codes or "FIN_INVESTMENT_GUARANTEE" in codes:
        threat_reasons.append("promising guaranteed abnormal returns for simple tasks or VIP stock tips")
        recommendations.append("Do not deposit money to unlock tasks or join unverified investment groups.")
        verify_steps.append("Verify financial advisors against the official SEBI public register (sebi.gov.in).")

    if "FIN_INSTANT_LOAN_UPFRONT" in codes:
        threat_reasons.append("offering loans without credit checks while demanding an upfront processing fee")
        recommendations.append("Never pay advance fees or processing charges to receive a loan.")
        verify_steps.append("Verify lending entities against the RBI list of registered non-banking financial companies (NBFCs).")

    if "FIN_LOTTERY_ADVANCE_FEE" in codes:
        threat_reasons.append("announcing a lottery win or lucky draw requiring GST or release fees")
        recommendations.append("Do not pay advance tax or release charges. Genuine lotteries never demand fees to release prizes.")
        verify_steps.append("Check official contest organizers directly; unsolicited lottery alerts are standard advance-fee scams.")

    if "FAMILY_EMERGENCY_IMPERSONATION" in codes:
        threat_reasons.append("impersonating a family member in distress claiming a broken phone to solicit urgent funds")
        recommendations.append("Do not transfer money to the provided handle or account.")
        verify_steps.append("Call your family member directly on their known regular phone number or contact another family member first.")

    if "CRED_CARD_DETAILS_PROMPT" in codes:
        threat_reasons.append("prompting you to submit payment card or banking credentials under false billing failure claims")
        recommendations.append("Do not enter credit or debit card details through links sent in messages.")
        verify_steps.append("Open the official streaming or service website yourself to review your subscription billing state.")

    if any(u.get("is_deceptive") for u in urls):
        threat_reasons.append("including a deceptive or lookalike link designed to mimic an authentic service")
        recommendations.append("Do NOT open the link. Fraudulent domains capture credentials and sensitive financial data.")
        verify_steps.append("Type the organization's official website URL directly into your web browser.")
    elif any(u.get("is_shortener") for u in urls):
        threat_reasons.append("containing an obfuscated link shortener hiding its true destination")
        recommendations.append("Avoid opening shortened links from unknown or unverified senders.")
        verify_steps.append("Inspect the actual domain using link expansion tools or request the full unshortened URL.")

    if "URGENCY_PRESSURE" in codes and not threat_reasons:
        threat_reasons.append("applying high psychological pressure and short deadlines to force hasty action")
        recommendations.append("Pause before acting. Urgency is designed to bypass careful verification.")
        verify_steps.append("Contact the official customer care of the claimed service using numbers from their verified website.")

    if not threat_reasons:
        threat_reasons.append("carrying patterns characteristic of unsolicited suspicious communication")
        recommendations.append("Exercise caution and avoid sharing personal information or transferring funds.")
        verify_steps.append("Confirm the authenticity directly with the claimed institution through official channels.")

    summary = f"Threats Detected: This communication was flagged for {'; '.join(threat_reasons)}."

    return {
        "summary": summary,
        "recommendations": recommendations,
        "verify_steps": verify_steps,
    }
