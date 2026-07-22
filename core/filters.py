"""
filters.py — Job title and description keyword filters.
"""

MATCH_THRESHOLD = 0.75


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
