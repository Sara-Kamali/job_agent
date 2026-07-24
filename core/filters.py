"""
filters.py — Job title and description keyword filters.
"""
import re

MATCH_THRESHOLD = 0.80


def title_matches(title: str, keywords: list = None) -> bool:
    """
    Return True if the job title contains any of the required keywords.

    Args:
        title: job title string
        keywords: list of keywords to match; returns True (match all) if None or empty
    """
    if not keywords:
        return True
    clean_keywords = [kw.strip().lower() for kw in keywords if kw and kw.strip()]
    if not clean_keywords:
        return True
    t = title.lower()
    return any(kw in t for kw in clean_keywords)


def description_matches(description: str, keywords: list = None) -> bool:
    """
    Return True if the job description contains any of the required keywords.

    Args:
        description: job description string
        keywords: list of keywords or phrases to match; returns True if None or empty
    """
    if not keywords:
        return True
    clean_keywords = [kw.strip().lower() for kw in keywords if kw and kw.strip()]
    if not clean_keywords:
        return True
    d = (description or "").lower()
    return any(kw in d for kw in clean_keywords)


# Default terms used to detect a PhD / doctorate mention in a job description.
PHD_KEYWORDS = [
    "phd", "ph.d", "ph. d", "ph.d.", "d.phil", "dphil",
    "doctorate", "doctoral", "doctoral degree",
]


# Slightly broader than PHD_KEYWORDS: used only to DECIDE whether to show the
# "PhD level" badge on a job card, never to filter jobs out. Includes
# "graduate degree" per the badge spec, which PHD_KEYWORDS deliberately
# excludes (too broad to use as a hard filter — most Master's roles say this).
BADGE_PHD_KEYWORDS = PHD_KEYWORDS + ["graduate degree"]


def is_phd_level(description: str, title: str = "") -> bool:
    """
    Returns True if the job mentions a PhD, doctorate, or graduate degree
    anywhere in the title or description. Used only to show a badge — this
    never removes a job from the digest.
    """
    text = f"{title} {description}".lower()
    return any(k in text for k in BADGE_PHD_KEYWORDS)


def phd_matches(description: str, enabled: bool = False, keywords: list = None) -> bool:
    """
    When enabled, return True only if the description mentions a PhD / doctorate.
    When disabled, always return True (no filtering).

    Args:
        description: job description string
        enabled: if False, this filter is a no-op and everything passes
        keywords: PhD/doctorate terms to look for; defaults to PHD_KEYWORDS
    """
    if not enabled:
        return True
    kw = keywords if keywords else PHD_KEYWORDS
    clean = [k.strip().lower() for k in kw if k and k.strip()]
    d = (description or "").lower()
    return any(k in d for k in clean)


# LENIENT exclusions: topics that are fine to mention in passing, but not as the
# job's main focus. Phrases, not bare words, so "medical imaging" survives.
DEFAULT_EXCLUDE_KEYWORDS = [
    # LLM / NLP / generative text
    "large language model", "llm", "llms", "genai", "generative ai", "gpt",
    "natural language processing", "nlp", "chatbot", "prompt engineering",
    "conversational ai", "text generation", "retrieval-augmented",
    # computer vision / generative image
    "computer vision", "image generation", "text-to-image", "diffusion model",
    "object detection", "image recognition", "visual recognition",
    "stable diffusion", "image synthesis", "generative image",
]

# STRICT exclusions: hard blockers. A SINGLE mention anywhere drops the job,
# because these disqualify the role outright rather than just shifting its focus.
DEFAULT_HARD_EXCLUDE_KEYWORDS = [
    "military", "defense contractor", "defence contractor", "defense sector",
    "defence sector", "weapons", "warfare", "combat systems", "missile",
    "security clearance", "top secret", "classified clearance",
    "department of defense", "ministry of defence", "aerospace and defense",
    "aerospace and defence", "cbrne", "battlefield", "munitions",
    "national security", "homeland security", "defense industry",
    "defence industry", "defense sciences", "defence sciences",
    "armed forces", "counterterrorism", "counter-terrorism",
    " defense ", " defence ", "defense agency", "defence agency",
]


def should_exclude(title: str, description: str, keywords: list = None,
                   hard_keywords: list = None, min_desc_hits: int = 3) -> bool:
    """
    Returns True if the job should be dropped.

    Two tiers:
      - HARD blockers (military/defense/clearance): any single mention in the
        title or description drops the job.
      - LENIENT topics (LLM/vision): dropped only when clearly the MAIN focus,
        meaning the phrase is in the TITLE, or appears >= min_desc_hits times
        in the description. One passing mention survives.

    Args:
        title: job title string
        description: job description string
        keywords: lenient phrases; defaults to DEFAULT_EXCLUDE_KEYWORDS
        hard_keywords: strict phrases; defaults to DEFAULT_HARD_EXCLUDE_KEYWORDS
        min_desc_hits: description occurrences that count as "main focus"
    """
    t = (title or "").lower()
    d = (description or "").lower()

    # Tier 1: hard blockers — any mention at all.
    hard = hard_keywords if hard_keywords is not None else DEFAULT_HARD_EXCLUDE_KEYWORDS
    hard_clean = [k.strip().lower() for k in hard if k and k.strip()]
    combined = f"{t} {d}"
    if any(k in combined for k in hard_clean):
        return True

    # Tier 2: lenient topics — title match, or repeated in description.
    kw = keywords if keywords is not None else DEFAULT_EXCLUDE_KEYWORDS
    clean = [k.strip().lower() for k in kw if k and k.strip()]
    if not clean:
        return False
    if any(k in t for k in clean):
        return True
    hits = sum(d.count(k) for k in clean)
    return hits >= min_desc_hits


# Matches salary-looking figures: optional currency symbol/code, digits with
# separators, optional "k". Examples: 60,000  €60000  GBP 75k  85 000
_SALARY_RE = re.compile(
    r"(?:[€£$]|eur|gbp|usd|cad|aud|chf)?\s*"
    r"(\d{1,3}(?:[.,\s]\d{3})+|\d{2,7})"
    r"\s*(k\b)?",
    re.IGNORECASE,
)

# Only treat a number as an annual salary if it lands in a plausible range.
# Anything below this is likely an hourly rate, a year, or a headcount.
_MIN_PLAUSIBLE_ANNUAL = 10000
_MAX_PLAUSIBLE_ANNUAL = 1000000


def extract_salaries(text: str) -> list:
    """
    Pull plausible annual salary figures out of free text, currency-agnostic.
    Handles 60,000 / 60.000 / 60 000 / 60k / €60000 / GBP 75k.
    Returns a list of ints. Empty list means no salary was stated.
    """
    if not text:
        return []
    found = []
    for m in _SALARY_RE.finditer(text):
        raw, k_suffix = m.group(1), m.group(2)
        digits = re.sub(r"[.,\s]", "", raw)
        if not digits.isdigit():
            continue
        value = int(digits)
        if k_suffix:
            value *= 1000
        if _MIN_PLAUSIBLE_ANNUAL <= value <= _MAX_PLAUSIBLE_ANNUAL:
            found.append(value)
    return found


def salary_ok(text: str, minimum: int = 0) -> bool:
    """
    Returns True if the job passes the salary floor.

    IMPORTANT: jobs that state NO salary always pass. Most postings omit salary
    entirely, so rejecting them would discard the majority of real listings.
    A job is only rejected when a salary IS stated and its highest figure falls
    below `minimum`. Comparison is currency-agnostic (a raw number check), so
    set the floor in whatever currency you mostly see.
    """
    if not minimum:
        return True
    salaries = extract_salaries(text)
    if not salaries:
        return True  # no salary stated -> keep
    return max(salaries) >= minimum
