# Job Agent — PhD-Focused Fork

Job Agent searches multiple job boards, filters listings against your
preferred roles, locations, and requirements, scores the remaining jobs
against your CV using a locally running Ollama model, and shows the results
in a browser digest. Everything runs on your machine; your CV and job data
never leave it, and no hosted language-model account is required.

This is a fork of the original **Job Agent** by
**[maralthesage](https://github.com/maralthesage)**. This README covers only
what this fork adds. For installation basics, project structure, the
original LinkedIn/Stepstone/Xing scrapers, and general troubleshooting, see
the [original repository](https://github.com/maralthesage/job_agent).

## Requirements

- macOS, Python 3.10+, Chromium for Playwright (see the original repo for
  full setup).
- **[Ollama](https://ollama.com/download)**, running locally. This is what
  scores each job against your CV, entirely on your machine.

  Install it, then in a terminal:
  ```bash
  ollama serve
  ```
  If it reports the address is already in use, Ollama is already running,
  nothing to fix.

  Pull a model to score with (the app defaults to `gemma4:e4b`; any
  installed model works):
  ```bash
  ollama pull gemma4:e4b
  ollama list          # see what's already on your machine
  ```
  To use a different model for a run:
  ```bash
  OLLAMA_MODEL=<model-name> python main.py --run
  ```

## What This Fork Adds

### Job boards

- **Reed** (`scrapers/reed.py`) — UK, nationwide, via Reed's official
  Jobseeker API. Requires a free API key:
  ```bash
  echo 'export REED_API_KEY=your-key-here' >> ~/.zshrc
  source ~/.zshrc
  ```
  Register at reed.co.uk/developers/jobseeker. Without the key, Reed logs a
  notice and returns nothing; every other board still runs.

- **Job Bank** (`scrapers/jobbank.py`) — Canada, via the official RSS feed,
  restricted to postings explicitly open to international candidates. No key
  needed.

- **Himalayas** (`scrapers/himalayas.py`) — worldwide remote, via a free
  public JSON API, no key needed.

Reed, Job Bank, and Himalayas ignore the `locations` config setting by
design: Reed searches the whole UK, Job Bank is pinned to
international-candidate listings, Himalayas is pinned to no-geo-restriction
roles.

**These three boards, and every option below, only work through
`data/user_config.json`.** The inherited browser settings page
(`/settings`) only knows about LinkedIn, Stepstone, and Xing. Run with:

```bash
cp data/user_config.example.json data/user_config.json   # first time only
python main.py --run
```

### Filters (all configured in `data/user_config.json`)

- **`min_salary`** — currency-agnostic minimum salary floor (handles
  `60,000`, `90.000`, `75k`, `EUR 60000`, etc.). Jobs stating **no** salary
  always pass, since most postings omit it; only a job that states a figure
  below the floor is removed. `0` disables it.

- **`exclude_keywords`** / **`hard_exclude_keywords`** — topic exclusion,
  two tiers. `exclude_keywords` (default: LLM/NLP/generative-text and
  computer-vision terms) removes a job only when the term is in the title or
  appears 3+ times in the description, so a passing mention or something
  like "medical imaging" survives. `hard_exclude_keywords` (default:
  military, defense, weapons, national security, security clearance, etc.)
  removes a job on a **single** mention anywhere. Set `exclude_focus: false`
  to turn both off.

- **PhD indicator** — jobs whose title or description mention a PhD,
  doctorate, or graduate degree get a pink **⭐ PhD level** badge on their
  card in the digest. This is informational only; it does not filter
  anything out, so nothing is ever hidden because it might require a PhD.
  A stricter opt-in hard filter also exists (`"require_phd": true`), which
  removes any job that does *not* mention a PhD/doctorate — off by default,
  since Reed and Job Bank return short description snippets and this can
  cut relevant jobs that mention it further down the full posting.

- **`match_threshold`** — this fork's default is `0.80`, stricter than the
  original's `0.75`.

### The digest

- **New / Seen columns** — every job starts under **New**. Clicking
  **View Job** moves it to **Seen** immediately and permanently; simply
  loading the page does not mark anything as seen.
- **Select and delete** — check one or more jobs and a toolbar appears with
  **Delete selected**. This is a soft delete: the row stays in the database
  (so a deleted job is never re-scraped and re-added), it just never
  appears in the digest again.
- **Status bars** — a dark bar shows raw scraping progress; a yellow bar
  reports new jobs that have cleared your match threshold and is safe to
  click any time, it never reloads the page on its own.
- The digest (`http://localhost:8765/digest`) opens automatically when the
  app starts.

## Troubleshooting Specific to This Fork

**Config changes have no effect / `cv_text_len=0` at startup.** Almost
always invalid JSON in `data/user_config.json`, usually curly quotes from a
word processor instead of straight `"` quotes, or Python's `True`/`False`
instead of JSON's lowercase `true`/`false`. Validate directly:
```bash
python3 -c "import json; json.load(open('data/user_config.json')); print('valid')"
```

**`playwright not installed` / boards return 0 listings.** The virtual
environment isn't active in the current terminal:
```bash
source venv/bin/activate
```

**Old jobs keep appearing.** The digest shows every stored job above
threshold, not just the latest run. Delete unwanted ones from the digest, or
wipe the database:
```bash
sqlite3 data/jobs.db "DELETE FROM seen_jobs;"
```

For anything not covered here, see the
[original project's README](https://github.com/maralthesage/job_agent).
