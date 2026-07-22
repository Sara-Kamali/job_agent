"""
jobbank.py — Canada Job Bank scraper via the official RSS feed.

Job Bank (the Government of Canada's job board) publishes an RSS feed that
honours the same filters as the website. We pin fglo=1, which limits results
to jobs open to international candidates — the only Job Bank postings you can
apply to without existing Canadian work authorization.

Feed:   https://www.jobbank.gc.ca/jobsearch/feed/jobSearchRSSfeed
Params: dkw=<keyword>  fglo=1 (international)  sort=D (newest)  rows=<count>
"""
import asyncio
import re
from typing import List, Dict
from xml.etree import ElementTree

from scrapers.common import make_job_id, clean_text

FEED_URL = "https://www.jobbank.gc.ca/jobsearch/feed/jobSearchRSSfeed"
ROWS_PER_ROLE = 100


def _strip_html(text: str) -> str:
    return clean_text(re.sub(r"<[^>]+>", " ", text or ""))


async def scrape_jobbank(max_jobs: int = 20, on_job=None, roles: List[str] = None, locations: List[str] = None) -> List[Dict]:
    """
    Returns list of job dicts: {id, source, title, company, location, url, description}.

    locations is accepted for interface compatibility but unused: fglo=1 already
    scopes results to all-Canada jobs open to international candidates, which is
    the relevant slice for a candidate needing sponsorship.
    """
    if not roles:
        print("[JobBank] No roles configured. Add role keywords in your settings.")
        return []

    try:
        import httpx
    except ImportError:
        print("[JobBank] httpx not installed. Run: pip install httpx")
        return []

    jobs: List[Dict] = []
    seen_urls = set()

    async with httpx.AsyncClient(timeout=30, headers={"User-Agent": "Mozilla/5.0 (job_agent)"}) as client:
        for role in roles:
            if len(jobs) >= max_jobs:
                break
            params = {
                "dkw": role,   # keyword
                "fglo": 1,     # only jobs open to international candidates
                "sort": "D",   # newest first
                "rows": ROWS_PER_ROLE,
            }
            try:
                resp = await client.get(FEED_URL, params=params)
                resp.raise_for_status()
                root = ElementTree.fromstring(resp.content)
            except Exception as e:
                print(f"[JobBank] feed error for '{role}': {e}")
                continue

            for item in root.iter("item"):
                if len(jobs) >= max_jobs:
                    break
                link = (item.findtext("link") or "").strip()
                # Strip any jsessionid fragment so ids/dedupe stay stable.
                link = re.sub(r";jsessionid=[^?]*", "", link)
                if not link or link in seen_urls:
                    continue
                seen_urls.add(link)

                raw_title = clean_text(item.findtext("title") or "")
                description = _strip_html(item.findtext("description") or "")

                # RSS titles pack several fields, e.g.:
                #   "Data Scientist - Company Name - Location (ON)"
                # Best-effort split; the scorer works mainly off title + description.
                parts = [p.strip() for p in raw_title.split(" - ") if p.strip()]
                title = parts[0] if parts else raw_title
                company = parts[1] if len(parts) > 1 else ""
                location = parts[-1] if len(parts) > 2 else "Canada"

                if not title:
                    continue

                job = {
                    "id": make_job_id("jobbank", link),
                    "source": "jobbank",
                    "title": title,
                    "company": company,
                    "location": location or "Canada",
                    "url": link,
                    "description": description or raw_title,
                }
                jobs.append(job)
                if on_job:
                    on_job(job)

            await asyncio.sleep(1)

    print(f"[JobBank] collected {len(jobs)} listings (international-candidate jobs only)")
    return jobs
