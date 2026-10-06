from typing import Dict, Any, Optional
import re

from app.engine.normalize import normalize_text, detect_language
from app.engine.extractors import extract_urls, extract_upi_details, extract_phone_numbers
from app.engine.analyzers.concept_rules import analyze_concept_combinations
from app.engine.analyzers.text_rules import Indicator
from app.engine.analyzers.legitimacy import analyze_legitimacy
from app.engine.scoring import calculate_score
from app.engine.explain import build_explanation


class DetectionEngine:
    """
    GARUDA Multi-Modal Scam and Suspicious Content Detection Engine (v2.0.0).
    Pure Python framework-free detection engine (no FastAPI imports).
    Executes the full pipeline:
    Input -> Validate -> Normalize -> Extract -> Rules + Legitimacy -> Scorer -> Explainer -> AnalysisResult
    """

    def __init__(self, version: str = "2.0.0"):
        self.version = version

    def analyze(self, raw_text: str, scan_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyzes a message text for scam, phishing, fraud, and legitimacy indicators.
        Returns complete analysis payload matching ARCHITECTURE Section 6 & 8.
        """
        # 1. Validation & Unusable check
        stripped = (raw_text or "").strip()
        has_alphanumeric = bool(re.search(r"[a-zA-Z0-9\u0900-\u097F\u0C00-\u0C7F]", stripped))
        is_unusable = not stripped or not has_alphanumeric

        # 2. Normalize
        clean_text, search_text = normalize_text(stripped)
        detected_lang, lang_confidence = detect_language(clean_text)

        # 3. Extract entities (URLs, UPI, Phones)
        extracted_urls = extract_urls(clean_text) if not is_unusable else []
        extracted_upi = extract_upi_details(clean_text) if not is_unusable else {"vpas": [], "amounts": []}
        extracted_phones = extract_phone_numbers(clean_text) if not is_unusable else []

        # 4. Analyze Concept Combinations (Threat Indicators)
        risk_indicators = []
        if not is_unusable:
            risk_indicators = analyze_concept_combinations(search_text, clean_text)

            # URL-derived threat indicators
            for url_info in extracted_urls:
                if url_info.get("is_deceptive"):
                    risk_indicators.append(
                        Indicator(
                            code="DECEPTIVE_URL_DETECTED",
                            label="Deceptive or impersonated destination link",
                            severity="high",
                            weight=0.55,
                            evidence=url_info["raw"],
                        )
                    )
                elif url_info.get("is_shortener"):
                    risk_indicators.append(
                        Indicator(
                            code="URL_SHORTENER_DETECTED",
                            label="Obfuscated link shortener obscuring destination",
                            severity="low",
                            weight=0.30,
                            evidence=url_info["raw"],
                        )
                    )

        # 5. Analyze Legitimacy Signals
        legitimacy_signals = []
        if not is_unusable:
            legitimacy_signals = analyze_legitimacy(search_text, clean_text, extracted_urls)

        # 6. Scoring (Noisy-OR with Anti-Gaming Rules)
        score_data = calculate_score(
            risk_indicators=risk_indicators,
            legitimacy_signals=legitimacy_signals,
            intel_hits=0,
            is_unusable=is_unusable,
        )

        risk_level = score_data["level"]
        risk_score = score_data["score"]
        risk_label = score_data["label"]
        category = score_data["category"]

        # Confidence assessment
        if is_unusable:
            confidence = 0.50
        elif len(clean_text) < 20 and not risk_indicators:
            confidence = 0.70
        else:
            confidence = round(min(0.95, lang_confidence * 0.98), 2)

        # 7. Verification Status
        # Architecture Rule: Never "verified safe", always honest verification status
        if is_unusable:
            verification_status = "unable_to_verify"
        elif any(u.get("is_deceptive") for u in extracted_urls):
            verification_status = "unverified_deceptive_destination"
        else:
            verification_status = "unverified"

        # 8. Dynamic Explanation
        explanation = build_explanation(
            indicators=risk_indicators,
            legitimacy_signals=legitimacy_signals,
            risk_level=risk_level,
            urls=extracted_urls,
        )

        return {
            "scan_id": scan_id,
            "scan_type": "message",
            "risk": {
                "score": risk_score,
                "level": risk_level,
                "label": risk_label,
            },
            "confidence": confidence,
            "verification_status": verification_status,
            "category": category,
            "summary": explanation["summary"],
            "indicators": [ind.to_dict() for ind in risk_indicators],
            "legitimacy_signals": [leg.to_dict() for leg in legitimacy_signals],
            "recommendations": explanation["recommendations"],
            "verify_steps": explanation["verify_steps"],
            "extracted": {
                "urls": extracted_urls,
                "qr": None,
                "upi": extracted_upi,
                "phone": extracted_phones,
                "language": detected_lang,
            },
            "intel": [
                {
                    "source": "garuda_blocklists",
                    "status": "not_found",
                }
            ],
            "engine_version": self.version,
        }


# Global singleton engine instance
engine = DetectionEngine()
