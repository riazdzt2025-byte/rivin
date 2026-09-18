"""
Geo helpers — country -> language.
PROMPT section 3. Pure functions, easy to test.
"""
from __future__ import annotations

ARABIC_COUNTRIES = {
    "SA", "AE", "EG", "KW", "QA", "BH", "OM", "YE", "JO", "LB",
    "SY", "IQ", "LY", "SD", "MA", "DZ", "TN", "PS", "MR", "SO",
    "DJ", "KM", "TD", "ER",
}
# Explicit: only BD -> bn. IN falls through to Accept-Language.
BENGALI_COUNTRIES = {"BD"}
ENGLISH_COUNTRIES = {"US", "GB", "CA", "AU", "IE", "NZ", "SG", "PH", "ZA", "MY", "IN", "NG", "KE"}

SUPPORTED = ("bn", "en", "ar")
DEFAULT_LANGUAGE = "bn"

COUNTRY_HEADERS = (
    "HTTP_CF_IPCOUNTRY",         # Cloudflare
    "HTTP_X_VERCEL_IP_COUNTRY",  # Vercel
    "HTTP_X_COUNTRY_CODE",       # generic nginx geoip
    "HTTP_X_GEO_COUNTRY",
    "HTTP_X_NF_COUNTRY",         # harmless, Netlify-like
)

def normalize_country(code: str | None) -> str | None:
    if not code:
        return None
    c = code.strip().upper()
    if len(c) != 2 or not c.isalpha():
        return None
    return c

def language_for_country(country: str | None) -> str | None:
    c = normalize_country(country)
    if not c:
        return None
    if c in BENGALI_COUNTRIES:
        return "bn"
    if c in ARABIC_COUNTRIES:
        return "ar"
    if c in ENGLISH_COUNTRIES:
        return "en"
    # Unknown country -> no opinion, caller falls back to Accept-Language
    return None

def language_from_accept_language(header: str | None) -> str | None:
    if not header:
        return None
    scored: list[tuple[float, str]] = []
    for part in header.split(","):
        part = part.strip()
        if not part:
            continue
        if ";q=" in part:
            tag, _, q_str = part.partition(";q=")
            tag = tag.strip()
            q_str = q_str.strip()
            try:
                q = float(q_str)
            except ValueError:
                q = 0.0
        else:
            tag = part
            q = 1.0
        # tag like "bn-BD" or "ar" -> take primary subtag
        primary = tag.split("-")[0].split("_")[0].lower()
        if len(primary) == 2 and primary in SUPPORTED:
            scored.append((q, primary))
        elif primary in SUPPORTED:
            scored.append((q, primary))
    if not scored:
        return None
    # sort by q desc, stable for equal q (keep original order)
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]

def country_from_request(request) -> str | None:
    for h in COUNTRY_HEADERS:
        val = request.META.get(h)
        if val:
            n = normalize_country(val)
            if n:
                return n
    return None
