"""
GARUDA URL Analyzer
===================
Checks a web address for signs of phishing, fake brands, illegal betting
and adult content - WITHOUT ever opening the website (static analysis only).

How it works (in 5 steps):
  1. validate_and_normalize()  -> is it a real web address? clean it up
  2. registered_domain()       -> find the "main" domain (indian.1xbet.com -> 1xbet.com)
  3. run checks                -> each check that fires adds an "indicator" with a weight
  4. noisy-OR score            -> combine the weights into one 0-100 risk score
  5. build the result          -> level, category, reasons, advice

Only Python's standard library is used, so nothing extra to install.
"""

from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass, field
from urllib.parse import urlsplit, parse_qs

ENGINE_VERSION = "url-1.0.0"

# ---------------------------------------------------------------------------
# 1. Reference lists  (later these can move to YAML files / the database)
# ---------------------------------------------------------------------------

# Country "endings" made of two parts. Needed so sbi.co.in -> sbi.co.in (not co.in)
MULTI_PART_SUFFIXES = {
    "co.in", "gov.in", "nic.in", "org.in", "net.in", "ac.in", "edu.in",
    "res.in", "firm.in", "gen.in", "ind.in", "co.uk", "org.uk", "com.au",
}

# Official domains that must NEVER be flagged as fake
OFFICIAL_DOMAINS = {
    # banks
    "sbi.co.in", "onlinesbi.sbi", "sbi", "hdfcbank.com", "icicibank.com",
    "axisbank.com", "kotak.com", "pnbindia.in", "bankofbaroda.in", "canarabank.com",
    "unionbankofindia.co.in", "idfcfirstbank.com", "yesbank.in", "indusind.com",
    # payments / UPI
    "paytm.com", "paytmmall.com", "phonepe.com", "google.com", "npci.org.in", "bhimupi.org.in",
    "amazon.in", "amazon.com", "flipkart.com",
    # telecom
    "airtel.in", "jio.com", "myvi.in", "bsnl.co.in",
    # government / regulators
    "rbi.org.in", "sebi.gov.in", "uidai.gov.in", "incometax.gov.in",
    "irctc.co.in", "digilocker.gov.in", "cybercrime.gov.in", "indiapost.gov.in",
    # common safe sites
    "youtube.com", "wikipedia.org", "microsoft.com", "apple.com", "github.com",
}
OFFICIAL_SUFFIXES = (".gov.in", ".nic.in")  # any government site

# Brand words scammers copy into fake domains -> the real domain(s)
BRANDS = {
    "sbi": {"sbi.co.in", "onlinesbi.sbi", "sbi"},
    "hdfc": {"hdfcbank.com"},
    "icici": {"icicibank.com"},
    "axis": {"axisbank.com"},
    "kotak": {"kotak.com"},
    "paytm": {"paytm.com"},
    "phonepe": {"phonepe.com"},
    "gpay": {"google.com"},
    "amazon": {"amazon.in", "amazon.com"},
    "flipkart": {"flipkart.com"},
    "airtel": {"airtel.in"},
    "jio": {"jio.com"},
    "irctc": {"irctc.co.in"},
    "aadhaar": {"uidai.gov.in"},
    "uidai": {"uidai.gov.in"},
    "incometax": {"incometax.gov.in"},
    "indiapost": {"indiapost.gov.in"},
    "netflix": {"netflix.com"},
}

# Curated Indian illegal-betting brands (matched on the main domain name)
BETTING_BRANDS = {
    "1xbet", "parimatch", "betway", "stake", "lotus365", "mahadevbook",
    "dafabet", "4rabet", "10cric", "fairplay", "melbet", "mostbet", "1win",
    "bet365", "reddyanna", "dream11bet",
}

# Small starter adult list (the full blocklist loader adds thousands later)
ADULT_KEYWORDS = {"porn", "xxx", "xvideos", "xnxx", "xhamster", "redtube"}

URL_SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "cutt.ly", "is.gd", "ow.ly",
    "rb.gy", "shorturl.at", "tiny.cc", "rebrand.ly", "t.ly",
}

RISKY_TLDS = {
    "xyz", "top", "click", "link", "work", "loan", "online", "site", "live",
    "buzz", "rest", "gq", "tk", "ml", "cf", "ga", "icu", "cyou", "shop", "monster",
}

SUSPICIOUS_PARAMS = {"pin", "otp", "password", "pass", "cvv", "upi_pin", "mpin"}
SUSPICIOUS_PATH_WORDS = {"kyc", "verify", "update", "login", "secure", "unlock",
                         "reward", "refund", "claim", "account", "blocked"}

# ---------------------------------------------------------------------------
# 2. Small data classes for the result
# ---------------------------------------------------------------------------

@dataclass
class Indicator:
    code: str
    label: str
    severity: str      # low | medium | high
    weight: float      # 0.0 - 0.9  (never 1.0: heuristics are never 100% certain)
    evidence: str


@dataclass
class UrlResult:
    input: str
    valid: bool
    normalized_url: str | None = None
    domain: str | None = None
    registered_domain: str | None = None
    score: int = 0
    level: str = "unable_to_verify"
    label: str = "Unable to Verify"
    category: str = "none"
    category_label: str = ""
    summary: str = ""
    indicators: list[Indicator] = field(default_factory=list)
    legitimacy_signals: list[Indicator] = field(default_factory=list)
    verification_status: str = "unverified"
    recommendations: list[str] = field(default_factory=list)
    error: str | None = None
    engine_version: str = ENGINE_VERSION

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        d["indicators"] = [i.__dict__ for i in self.indicators]
        d["legitimacy_signals"] = [i.__dict__ for i in self.legitimacy_signals]
        return d

# ---------------------------------------------------------------------------
# 3. Helpers
# ---------------------------------------------------------------------------

def validate_and_normalize(raw: str) -> tuple[str | None, str | None]:
    """Return (normalized_url, error). Never opens the URL."""
    text = (raw or "").strip()
    if not text:
        return None, "Please enter a web address."
    if " " in text:
        return None, "This doesn't look like a valid web address (it contains spaces)."
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", text):
        text = "https://" + text          # google.com -> https://google.com
    parts = urlsplit(text)
    if parts.scheme not in ("http", "https"):
        return None, f"Only http/https links can be checked (got '{parts.scheme}')."
    host = parts.hostname or ""
    if not host:
        return None, "This doesn't look like a valid web address (no domain)."
    if "." not in host and not _is_ip(host):
        return None, "This doesn't look like a valid web address (no domain ending like .com)."
    return text, None


def _is_ip(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


def registered_domain(host: str) -> str:
    """indian.1xbet.com -> 1xbet.com ; www.sbi.co.in -> sbi.co.in"""
    host = host.lower().rstrip(".")
    if _is_ip(host):
        return host
    labels = host.split(".")
    if len(labels) >= 3 and ".".join(labels[-2:]) in MULTI_PART_SUFFIXES:
        return ".".join(labels[-3:])
    return ".".join(labels[-2:]) if len(labels) >= 2 else host


def edit_distance(a: str, b: str) -> int:
    """How many single-letter edits (insert, delete, replace, swap two neighbours)
    turn a into b. 'flipkrat' -> 'flipkart' = 1 (one swap)."""
    d = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a) + 1):
        d[i][0] = i
    for j in range(len(b) + 1):
        d[0][j] = j
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            cost = a[i - 1] != b[j - 1]
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cost)
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + 1)
    return d[len(a)][len(b)]


# digits/symbols scammers use to imitate letters: amaz0n, paytrn, 1cici
LOOKALIKE_MAP = str.maketrans({"0": "o", "3": "e", "4": "a", "5": "s",
                               "7": "t", "@": "a", "$": "s"})


def lookalike_variants(text: str) -> list[str]:
    """'netf1ix' -> ['netfiix', 'netflix']  ('1' can imitate both 'i' and 'l')."""
    base = text.translate(LOOKALIKE_MAP).replace("-", "")
    return [base.replace("1", "i"), base.replace("1", "l")]


def is_official(reg_domain: str, host: str) -> bool:
    return reg_domain in OFFICIAL_DOMAINS or host.endswith(OFFICIAL_SUFFIXES)


def noisy_or(weights: list[float]) -> float:
    """Combine weights: 1 - (1-w1)(1-w2)... -> never exceeds 1, grows with each signal."""
    p = 1.0
    for w in weights:
        p *= (1 - w)
    return 1 - p


def band(score: int) -> tuple[str, str]:
    if score >= 65:
        return "high", "High Risk"
    if score >= 45:
        return "medium", "Medium Risk"
    if score >= 25:
        return "suspicious", "Suspicious"
    return "likely_safe", "Likely Safe"

# ---------------------------------------------------------------------------
# 4. The main function
# ---------------------------------------------------------------------------

def analyze_url(raw: str) -> UrlResult:
    url, error = validate_and_normalize(raw)
    if error:
        return UrlResult(
            input=raw, valid=False, error=error,
            summary="GARUDA could not check this input because it is not a valid web address.",
            recommendations=["Copy the full link exactly as you received it and try again."],
        )

    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    reg = registered_domain(host)
    name = reg.split(".")[0]                       # "1xbet" from "1xbet.com"
    res = UrlResult(input=raw, valid=True, normalized_url=url, domain=host, registered_domain=reg)
    ind = res.indicators
    official = is_official(reg, host)

    # --- A. Reputation lists -------------------------------------------------
    host_tokens = set(re.split(r"[.\-]", host))
    if name in BETTING_BRANDS or host_tokens & BETTING_BRANDS:
        res.category = "gambling"
        res.category_label = "Illegal Betting / Gambling Platform"
        res.verification_status = "matched_garuda_curated_betting_list"
        ind.append(Indicator("BLOCKLIST_GAMBLING", "Known online betting platform", "high", 0.85,
                             reg))
    elif any(k in host for k in ADULT_KEYWORDS):
        res.category = "adult"
        res.category_label = "Restricted Content (Adult)"
        res.verification_status = "matched_garuda_adult_keywords"
        ind.append(Indicator("BLOCKLIST_ADULT", "Adult website", "medium", 0.5, reg))

    # --- B. Structure checks (skipped for official domains) -----------------
    if not official:
        if _is_ip(host):
            ind.append(Indicator("URL_IP_HOST", "Uses a raw IP address instead of a name",
                                 "high", 0.5, host))
        if host.startswith("xn--") or ".xn--" in host:
            ind.append(Indicator("URL_PUNYCODE", "Uses special look-alike letters (punycode)",
                                 "high", 0.55, host))
        if "@" in (parts.netloc or ""):
            ind.append(Indicator("URL_AT_TRICK", "Hides the real address using '@'",
                                 "high", 0.5, parts.netloc))
        if host.count(".") >= 4:
            ind.append(Indicator("URL_DEEP_SUBDOMAINS", "Unusually many sub-domains",
                                 "medium", 0.25, host))
        tld = host.rsplit(".", 1)[-1]
        if tld in RISKY_TLDS:
            ind.append(Indicator("URL_RISKY_TLD", f"Domain ending '.{tld}' is often used in scams",
                                 "medium", 0.25, "." + tld))
        if reg in URL_SHORTENERS:
            ind.append(Indicator("URL_SHORTENER", "Short link hides the real destination",
                                 "low", 0.3, reg))
        if parts.scheme == "http":
            ind.append(Indicator("URL_NO_HTTPS", "Not encrypted (http instead of https)",
                                 "low", 0.1, "http://"))

        # Brand impersonation: brand word in the domain, but not the official domain
        variants = lookalike_variants(host)
        for brand, real_domains in BRANDS.items():
            if reg in real_domains:
                continue
            if any(brand in v for v in variants):
                ind.append(Indicator("URL_BRAND_IMPERSONATION",
                                     f"Uses the name '{brand.upper()}' but is not its official website",
                                     "high", 0.65, host))
                break
            # typo look-alikes like 'hdfcbnak' or 'flipkrat' (only for longer brands)
            if len(brand) >= 5 and any(
                    abs(len(tok) - len(brand)) <= 1 and 0 < edit_distance(tok, brand) <= 1
                    for v in variants for tok in re.split(r"[.]", v) if tok):
                ind.append(Indicator("URL_BRAND_LOOKALIKE",
                                     f"Looks like a misspelling of '{brand.upper()}'",
                                     "high", 0.65, host))
                break

        # Brand name hidden in the path of an IP or unknown site: 1.2.3.4/paytm/verify
        path_l = parts.path.lower()
        if not any(i.code.startswith("URL_BRAND") for i in ind):
            for brand in BRANDS:
                if re.search(rf"\b{brand}\b", path_l):
                    ind.append(Indicator("URL_BRAND_IN_PATH",
                                         f"Mentions '{brand.upper()}' in the link but is not its website",
                                         "medium", 0.3, parts.path))
                    break

        # Words in the path that appear in phishing links
        path_words = {w for w in re.split(r"[/\-_.?=&]", parts.path.lower()) if w}
        hits = sorted(path_words & SUSPICIOUS_PATH_WORDS)
        if hits and any(i.severity == "high" for i in ind):
            ind.append(Indicator("URL_PHISHING_PATH", "Link path uses login/KYC/reward words",
                                 "medium", 0.2, "/" + "/".join(hits)))

        # Asking for secrets in the link itself
        params = {k.lower() for k in parse_qs(parts.query).keys()}
        bad = sorted(params & SUSPICIOUS_PARAMS)
        if bad:
            ind.append(Indicator("URL_SECRET_PARAM", "Link asks for a PIN/OTP/password",
                                 "high", 0.5, "?" + "&".join(bad)))
    else:
        res.legitimacy_signals.append(
            Indicator("LEGIT_OFFICIAL_DOMAIN", "Official website of a known organisation",
                      "low", 0.0, reg))
        res.verification_status = "matched_official_domain_list"

    # --- C. Score ------------------------------------------------------------
    res.score = round(100 * noisy_or([i.weight for i in ind]))
    res.level, res.label = band(res.score)
    if res.category == "none" and any(i.severity == "high" for i in ind):
        res.category, res.category_label = "phishing", "Possible Phishing / Fake Website"
    elif res.category == "none" and ind:
        res.category, res.category_label = "suspicious_link", "Suspicious Link"

    # --- D. Explanation + advice ----------------------------------------------
    res.summary = _summary(res, official)
    res.recommendations = _advice(res)
    return res


def _summary(res: UrlResult, official: bool) -> str:
    if official:
        return (f"{res.registered_domain} is on GARUDA's list of official websites. "
                "Still, make sure you typed or opened it yourself and didn't follow a forwarded link.")
    if res.category == "gambling":
        return ("This is a known online betting platform. Real-money online betting is illegal in "
                "India, and you have no legal protection for money you deposit.")
    if res.category == "adult":
        return ("This is an adult website. Such sites often carry malicious ads, fake 'virus' "
                "pop-ups and subscription traps.")
    if not res.indicators:
        return ("No structural warning signs were found. This site was not found in GARUDA's "
                "reputation lists, which does not guarantee it is safe.")
    reasons = "; ".join(i.label.lower() for i in res.indicators[:3])
    return f"This link shows warning signs: {reasons}."


def _advice(res: UrlResult) -> list[str]:
    if res.level == "likely_safe":
        return ["Prefer typing the website address yourself instead of clicking links.",
                "Never share OTP, UPI PIN or passwords on any website you reached from a message."]
    advice = ["Do not open this link.", "Do not enter OTP, UPI PIN, card details or passwords."]
    if res.category == "gambling":
        advice.append("Do not deposit money. Report illegal betting at cybercrime.gov.in.")
    else:
        advice.append("If you already entered details, call your bank and the cyber helpline 1930.")
    return advice


if __name__ == "__main__":   # quick manual test:  python url_analyzer.py
    for u in ["sbi.co.in", "http://sbi-kyc-update.xyz/login", "https://indian.1xbet.com",
              "bit.ly/3abcXYZ", "xxx videos.com"]:
        r = analyze_url(u)
        print(f"{u:40} -> {r.score:3} {r.level:16} {r.category_label or r.error or ''}")
