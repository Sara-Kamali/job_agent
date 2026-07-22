"""
himalayas.py — Himalayas (worldwide remote) scraper via the free public JSON API.

No API key required. We use the search endpoint with worldwide=true, so results
are remote jobs with no geographic restriction — the ones you can take from
anywhere, which sidestep the visa question entirely.

Docs:     https://himalayas.app/docs/remote-jobs-api
Endpoint: https://himalayas.app/jobs/api/search
Params:   q=<keyword>  worldwide=true  sort=recent  page=<n>
The API is rate limited (429 if exceeded) and cached for 24h.
"""
import asyncio
import re
from typing import List, Dict

from scrapers.common import make_job_id, clean_text

SEARCH_URL = "https://himalayas.app/jobs/api/search"
PAGES_PER_ROLE = 2  # each page returns up to ~20 jobs


def _strip_html(text: str) -> str:
    return clean_text(re.sub(r"<[^>]+>", " ", text or ""))


def _location_label(location_restrictions) -> str:
    # An empty locationRestrictions array means open worldwide.
    if not location_restrictions:
        return "Remote (Worldwide)"
    names = [loc.get("name", "") for loc in location_restrictions if loc.get("name")]
    return "Remote - " + ", ".join(names) if names else "Remote"


async def scrape_himalayas(max_jobs: int = 20, on_job=None, roles: List[str] = None, locations: List[str] = None) -> List[Dict]:
    """
    Returns list of job dicts: {id, source, title, company, location, url, description}.

    locations is accepted for interface compatibility but unused: worldwide=true
    already scopes results to no-geo-restriction remote roles.
    """
    if not roles:
        print("[Himalayas] No roles configured. Add role keywords in your settings.")
        return []

    try:
        import httpx
    except ImportError:
        print("[Himalayas] httpx not installed. Run: pip install httpx")
        return []

    jobs: List[Dict] = []
    seen_urls = set()

    async with httpx.AsyncClient(timeout=30, headers={"User-Agent": "job_agent/1.0"}) as client:
        for role in roles:
            if len(jobs) >= max_jobs:
                break
            for page in range(1, PAGES_PER_ROLE + 1):
                if len(jobs) >= max_jobs:
                    break
                params = {"q": role, "worldwide": "true", "sort": "recent", "page": page}
                try:
                    resp = await client.get(SEARCH_URL, params=params)
                    if resp.status_code == 429:
                        print("[Himalayas] rate limited (429); waiting 60s")
                        await asyncio.sleep(60)
                        resp = await client.get(SEARCH_URL, params=params)
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e:
                    print(f"[Himalayas] search error for '{role}' page {page}: {e}")
                    break

                page_jobs = data.get("jobs", [])
                if not page_jobs:
                    break  # no more pages for this role

                for item in page_jobs:
                    if len(jobs) >= max_jobs:
                        break
                    url = (item.get("applicationLink") or "").strip()
                    if not url or url in seen_urls:
                        continue
                    seen_urls.add(url)

                    title = clean_text(item.get("title", ""))
                    company = clean_text(item.get("companyName", ""))
                    description = _strip_html(item.get("description") or item.get("excerpt") or "")
                    location = _location_label(item.get("locationRestrictions"))

                    if not title:
                        continue

                    job = {
                        "id": make_job_id("himalayas", url),
                        "source": "himalayas",
                        "title": title,
                        "company": company,
                        "location": location,
                        "url": url,
                        "description": description,
                    }
                    jobs.append(job)
                    if on_job:
                        on_job(job)

                await asyncio.sleep(1)  # polite delay + respect rate limit

    print(f"[Himalayas] collected {len(jobs)} listings")
    return jobs
