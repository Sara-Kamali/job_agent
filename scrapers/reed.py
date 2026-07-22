"""
reed.py — Reed.co.uk (UK) job scraper via Reed's official Jobseeker API.

Reed exposes a documented REST API, so this scraper makes clean HTTP calls
instead of driving a browser. You need a free API key:
  1. Register at https://www.reed.co.uk/developers/jobseeker
  2. Copy your API key
  3. Export it before running:  export REED_API_KEY=your-key-here

The API uses HTTP Basic auth with the API key as the username and a blank
password. Docs: https://www.reed.co.uk/developers/jobseeker
"""
import asyncio
import os
from typing import List, Dict

from scrapers.common import make_job_id, clean_text

SEARCH_URL = "https://www.reed.co.uk/api/1.0/search"
RESULTS_PER_ROLE = 25


async def scrape_reed(max_jobs: int = 20, on_job=None, roles: List[str] = None, locations: List[str] = None) -> List[Dict]:
    """
    Returns list of job dicts: {id, source, title, company, location, url, description}.

    locations is accepted for interface compatibility but intentionally unused:
    Reed is UK-wide, so we search each role across the whole UK (you're open to
    relocation within the UK). Uncomment locationName below to pin a city.
    """
    if not roles:
        print("[Reed] No roles configured. Add role keywords in your settings.")
        return []

    api_key = os.environ.get("REED_API_KEY", "").strip()
    if not api_key:
        print("[Reed] REED_API_KEY not set. Get a free key at "
              "https://www.reed.co.uk/developers/jobseeker then run: "
              "export REED_API_KEY=your-key")
        return []

    try:
        import httpx
    except ImportError:
        print("[Reed] httpx not installed. Run: pip install httpx")
        return []

    jobs: List[Dict] = []
    seen_urls = set()

    # Reed API: HTTP Basic auth, api_key as username, blank password.
    async with httpx.AsyncClient(auth=(api_key, ""), timeout=30) as client:
        for role in roles:
            if len(jobs) >= max_jobs:
                break
            params = {
                "keywords": role,
                "resultsToTake": RESULTS_PER_ROLE,
                # "locationName": "London",      # uncomment to restrict to a city
                # "distanceFromLocation": 15,     # miles, requires locationName
            }
            try:
                resp = await client.get(SEARCH_URL, params=params)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                print(f"[Reed] search error for '{role}': {e}")
                continue

            for item in data.get("results", []):
                if len(jobs) >= max_jobs:
                    break
                job_id = item.get("jobId")
                url = item.get("jobUrl") or (f"https://www.reed.co.uk/jobs/{job_id}" if job_id else "")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)

                title = clean_text(item.get("jobTitle", ""))
                company = clean_text(item.get("employerName", ""))
                location = clean_text(item.get("locationName", ""))

                # The search endpoint returns a truncated description snippet. It's
                # enough for keyword filtering + Ollama scoring. To pull the full
                # text, GET https://www.reed.co.uk/api/1.0/jobs/{jobId} per result.
                description = clean_text(item.get("jobDescription", ""))

                # Fold salary into the description so the scorer can see it.
                min_sal = item.get("minimumSalary")
                max_sal = item.get("maximumSalary")
                if min_sal or max_sal:
                    currency = item.get("currency", "GBP") or "GBP"
                    description = f"Salary: {min_sal or '?'}-{max_sal or '?'} {currency}. {description}"

                if not title:
                    continue

                job = {
                    "id": make_job_id("reed", url),
                    "source": "reed",
                    "title": title,
                    "company": company,
                    "location": location or "United Kingdom",
                    "url": url,
                    "description": description,
                }
                jobs.append(job)
                if on_job:
                    on_job(job)

            await asyncio.sleep(1)  # polite delay between role queries

    print(f"[Reed] collected {len(jobs)} listings")
    return jobs
