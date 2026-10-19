import pytest
from app.engine import engine


def test_prize_money_english_false_negatives():
    """Verify English prize money claims without action details are flagged Medium."""
    text = "Hi you have won an ammount of rupees 10000"
    res = engine.analyze(text)
    indicators = [ind["code"] for ind in res["indicators"]]
    assert "PRIZE_MONEY_CLAIM" in indicators, f"Expected PRIZE_MONEY_CLAIM in {indicators}"
    
    # Weight about 0.5, Medium if alone
    pm_ind = next(ind for ind in res["indicators"] if ind["code"] == "PRIZE_MONEY_CLAIM")
    assert 0.45 <= pm_ind["weight"] <= 0.55
    assert pm_ind["severity"] == "medium"
    assert res["risk"]["level"] in ("suspicious", "medium")
    assert res["risk"]["level"] == "medium"
    assert res["risk"]["score"] == 50


def test_prize_money_romanized_telugu():
    """Verify Romanized Telugu prize money claims without action details are flagged Medium."""
    text = "meru oka 10000 win aiyaru"
    res = engine.analyze(text)
    indicators = [ind["code"] for ind in res["indicators"]]
    assert "PRIZE_MONEY_CLAIM" in indicators, f"Expected PRIZE_MONEY_CLAIM in {indicators}"
    
    pm_ind = next(ind for ind in res["indicators"] if ind["code"] == "PRIZE_MONEY_CLAIM")
    assert pm_ind["severity"] == "medium"
    assert res["risk"]["level"] == "medium"
    assert res["risk"]["score"] == 50

    # Additional Telugu romanized variants
    telugu_variants = [
        "Meeru 25000 gelicharu",
        "Nuvvu 10000 rupees gelichav",
        "meeku 10000 vachindi",
        "meeru oka 50000 lottery gelicharu",
    ]
    for variant in telugu_variants:
        r = engine.analyze(variant)
        var_inds = [ind["code"] for ind in r["indicators"]]
        assert "PRIZE_MONEY_CLAIM" in var_inds, f"Failed for variant '{variant}'"
        assert r["risk"]["level"] in ("suspicious", "medium", "high")


def test_prize_money_hinglish():
    """Verify Hinglish prize money claims without action details are flagged Medium."""
    text = "Aap 10000 jeete hai"
    res = engine.analyze(text)
    indicators = [ind["code"] for ind in res["indicators"]]
    assert "PRIZE_MONEY_CLAIM" in indicators, f"Expected PRIZE_MONEY_CLAIM in {indicators}"
    assert res["risk"]["level"] == "medium"
    assert res["risk"]["score"] == 50

    hinglish_variants = [
        "Aapne 10000 jeeta",
        "Aap 50000 rupees jeete",
        "Badhai ho aap 25000 lottery jeete",
        "Aapko 10000 amount mila hai jeete",
    ]
    for variant in hinglish_variants:
        r = engine.analyze(variant)
        var_inds = [ind["code"] for ind in r["indicators"]]
        assert "PRIZE_MONEY_CLAIM" in var_inds, f"Failed for Hinglish variant '{variant}'"
        assert r["risk"]["level"] in ("suspicious", "medium", "high")


def test_prize_money_with_action_details_escalate_to_high():
    """
    Verify that if the message also has claim/pay/fee/link/call/click/share details,
    the severity escalates to High.
    """
    cases = [
        # English
        ("Hi you have won an ammount of rupees 10000 click link to claim", "high"),
        ("Hi you have won an ammount of rupees 10000 claim now", "high"),
        ("You won 10000 rupees! Call 9876543210 to claim your prize", "high"),
        ("You won Rs 50000 in lottery. Pay Rs 500 fee to claim", "high"),
        ("You won 10000 rupees. Share your bank details to receive", "high"),
        # Hinglish
        ("Aap 10000 jeete hai claim karne ke liye is link par click karein", "high"),
        ("Aap 50000 jeete hai turant is number pe call karein", "high"),
        ("Badhai ho aap 25000 jeete hai processing fee pay karein", "high"),
        ("Aap 10000 jeete hai apna OTP share karein", "high"),
        # Romanized Telugu
        ("meru oka 10000 win aiyaru ee link click chesi claim cheyandi", "high"),
        ("Meeru 25000 gelicharu ventane ee number ki call cheyandi", "high"),
        ("meeku 10000 vachindi fee pay chesi claim cheyandi", "high"),
        ("Nuvvu 10000 rupees gelichav mee UPI PIN enter cheyandi", "high"),
    ]

    for text, expected_level in cases:
        res = engine.analyze(text)
        indicators = [ind["code"] for ind in res["indicators"]]
        assert "PRIZE_MONEY_CLAIM" in indicators, f"Expected PRIZE_MONEY_CLAIM in {indicators} for '{text}'"
        pm_ind = next(ind for ind in res["indicators"] if ind["code"] == "PRIZE_MONEY_CLAIM")
        assert pm_ind["severity"] == "high", f"Expected high severity for '{text}', got {pm_ind['severity']}"
        assert res["risk"]["level"] in ("high", "critical"), f"Expected high/critical for '{text}', got {res['risk']['level']}"
        assert res["risk"]["score"] >= 65, f"Expected score >= 65 for '{text}', got {res['risk']['score']}"


def test_prize_money_misspellings_tolerated():
    """Tolerate common misspellings: ammount, amout, congrats, congratulation, lotery, prise."""
    cases = [
        # ammount & amout
        "You won an ammount of rupees 10000",
        "You won an amout of rupees 10000",
        # congrats & congratulation
        "congrats you won a prize of rs 50000",
        "congratulation you won 25000 rupees",
        # lotery
        "You won 50000 rupees in lotery",
        # prise
        "congrats you won a prise of rs 50000",
        # combination of misspellings
        "congrats you won an amout of 5000 in lotery prise",
    ]

    for text in cases:
        res = engine.analyze(text)
        indicators = [ind["code"] for ind in res["indicators"]]
        assert "PRIZE_MONEY_CLAIM" in indicators, f"Failed to match misspelling in '{text}'"
        assert res["risk"]["level"] in ("suspicious", "medium", "high")


def test_legit_messages_stay_likely_safe():
    """
    Legit messages must stay Likely Safe:
    - 'You won the match yesterday!'
    - 'Your account was credited with Rs 10000 salary'
    - 'HDFC: Rs 500 cashback credited to your card'
    """
    legit_cases = [
        "You won the match yesterday!",
        "Your account was credited with Rs 10000 salary",
        "HDFC: Rs 500 cashback credited to your card",
        "SBI: Rs 1500 cashback credited to your account ending in 1234",
        "Your card ending 4417 was credited with Rs 500 cashback",
    ]

    for text in legit_cases:
        res = engine.analyze(text)
        indicators = [ind["code"] for ind in res["indicators"]]
        level = res["risk"]["level"]
        score = res["risk"]["score"]
        assert level == "likely_safe", (
            f"Legit message failed: '{text}' scored {score} (level: {level}), indicators: {indicators}"
        )
        assert score <= 24, f"Legit message score must be <= 24: '{text}' scored {score}"
