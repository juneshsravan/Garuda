import math
from typing import List, Dict, Any, Tuple

from app.engine.analyzers.text_rules import Indicator
from app.engine.analyzers.legitimacy import LegitimacySignal
from app.engine.scoring.bands import get_risk_band, determine_category


def calculate_score(
    risk_indicators: List[Indicator],
    legitimacy_signals: List[LegitimacySignal],
    intel_hits: int = 0,
    is_unusable: bool = False,
) -> Dict[str, Any]:
    """
    Computes risk score using the ARCHITECTURE Section 8.5 mathematical formulation:
    R = 1 - Π(1 - wᵢ)          over risk indicators (noisy-OR)
    L = 1 - Π(1 - lⱼ)          over legitimacy signals, capped at 0.8
    score = round(100 × R × (1 - L))

    Anti-gaming rule:
    If any high-severity or critical indicator is present, L is ignored (set to 0).
    """
    if is_unusable:
        return {
            "score": 0,
            "raw_r": 0.0,
            "raw_l": 0.0,
            "level": "unable_to_verify",
            "label": "Unable to Verify",
            "category": {"code": "unverifiable", "label": "Unverifiable Content"},
            "anti_gaming_applied": False,
        }

    # 1. Noisy-OR over risk indicators: R = 1 - Π(1 - wᵢ)
    prod_not_r = 1.0
    has_high_severity = False
    for ind in risk_indicators:
        w = max(0.0, min(ind.weight, 0.99))
        prod_not_r *= (1.0 - w)
        if ind.severity in ("high", "critical"):
            has_high_severity = True

    r = 1.0 - prod_not_r

    # 2. Noisy-OR over legitimacy signals: L = 1 - Π(1 - lⱼ)
    prod_not_l = 1.0
    for leg in legitimacy_signals:
        l_val = max(0.0, min(leg.weight, 0.99))
        prod_not_l *= (1.0 - l_val)

    l_discount = min(1.0 - prod_not_l, 0.80)

    # 3. Anti-gaming enforcement:
    # No legitimacy discount if there is a credential request, fee demand, deceptive URL, or high/critical threat
    anti_gaming_applied = False
    has_cred_request = any("CRED" in ind.code for ind in risk_indicators)
    has_fee_demand = any("FEE" in ind.code for ind in risk_indicators)
    has_deceptive_url = any(ind.code == "DECEPTIVE_URL_DETECTED" for ind in risk_indicators)

    if has_high_severity or has_cred_request or has_fee_demand or has_deceptive_url:
        l_discount = 0.0
        anti_gaming_applied = True

    # 4. Final score calculation
    raw_score = 100.0 * r * (1.0 - l_discount)
    score = int(round(raw_score))
    score = max(0, min(100, score))

    # Critical eligibility: >= 85 AND (intel hit OR credential/payment + impersonation)
    has_impersonation = any("IMPERSONATION" in ind.code for ind in risk_indicators)
    has_cred_or_fee = any(
        ind.code in ("CRED_OTP_REQUEST", "CRED_PIN_REQUEST", "FIN_LOTTERY_ADVANCE_FEE", "FIN_INSTANT_LOAN_UPFRONT")
        for ind in risk_indicators
    )
    is_critical_eligible = (intel_hits > 0) or (has_impersonation and has_cred_or_fee)

    risk_level, label = get_risk_band(score, is_critical=is_critical_eligible)
    category = determine_category(risk_indicators, risk_level)

    return {
        "score": score,
        "raw_r": round(r, 4),
        "raw_l": round(l_discount, 4),
        "level": risk_level,
        "label": label,
        "category": category,
        "anti_gaming_applied": anti_gaming_applied,
    }
