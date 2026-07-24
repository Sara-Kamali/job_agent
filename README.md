# Job Agent — PhD-Focused Fork

Job Agent is a local job-search assistant for macOS. It searches multiple job
boards, filters listings based on your preferred roles, locations, and job
requirements, scores matching jobs against your CV using a locally running
Ollama model, and displays the results in a browser digest.

This repository is a fork of the original **Job Agent** project by
**[maralsage](https://github.com/maralthesage)**, customized for a PhD-oriented job search.

## What Is New in This Fork

**Additional job boards**

- Added support for **Reed** (UK, via Reed's official Jobseeker API).
- Added support for **Himalayas** (worldwide remote, via a free public JSON API).
- Added support for the **Government of Canada Job Bank**, restricted to
  postings open to international candidates.

**Additional filtering**

- Optional **PhD filter** that keeps only jobs mentioning a PhD or doctorate as
  required, preferred, or advantageous. Off by default.
- **Topic exclusions** that remove jobs focused on LLM/NLP or computer-vision
  work, and jobs in the military, defense, or security-clearance space.
- A currency-agnostic **minimum salary floor**.

**Digest interface**

- Two-column digest separating **New** from **Seen** listings.
- **Select and delete** listings you do not want to see again.
- Status bars showing scraping progress and newly found jobs, without the page
  reloading underneath you.
- The digest page opens automatically when the app starts.

The original LinkedIn, Stepstone, and Xing sources remain part of the project,
alongside the newly added sources.

## How It Works

1. The selected job boards are searched for new listings.
2. Each listing's **title** must contain one of your configured roles.
3. Each listing's **description** must contain at least one of your description
   keywords, when keywords are configured.
4. Optional filters are applied in order: the PhD filter (if enabled), topic
   exclusions, and the salary floor.
5. Ollama evaluates the remaining listings against your CV locally.
6. Jobs that meet the configured match threshold are shown in the browser
   digest.

Filters run **before** scoring. Anything removed in steps 2 to 4 is never sent
to the model, which keeps runs fast but also means an over-tight filter can
silently hide good jobs.

Your CV and job data remain on your machine. No hosted language-model account
is required.

## Supported Job Boards

| Board | Region | Access method | Key required |
|---|---|---|---|
| LinkedIn | Configured locations | Browser scraping | No |
| Stepstone | Configured locations | Browser scraping | No |
| Xing | Configured locations | Browser scraping | No |
| Reed | United Kingdom (nationwide) | Official REST API | Yes |
| Job Bank | Canada (international candidates only) | Official RSS feed | No |
| Himalayas | Worldwide remote | Public JSON API | No |

Reed, Job Bank, and Himalayas ignore the `locations` setting by design. Reed
searches the whole UK, Job Bank is pinned to jobs open to international
candidates, and Himalayas is pinned to roles with no geographic restriction.

Job-board availability and results can vary because external websites may
change their page structure or restrict automated access.

## The Digest

Open the digest at:

```text
http://localhost:8765/digest
```

This page opens automatically when the app starts.

**New and Seen columns.** Every job starts in **New**. Clicking **View Job**
opens the listing and immediately moves that card into **Seen**, where it stays
across sessions. Only jobs you have actually opened move over; simply loading
the page does not mark anything as seen.

**Deleting jobs.** Each card has a checkbox. Selecting one or more reveals a
toolbar with **Delete selected**. Deleted jobs disappear from the digest
permanently.

Deletion is a soft delete: the database row is kept and flagged rather than
removed. This is deliberate. The scraper treats any job already in the database
as already processed, so a kept row is what prevents a deleted job from being
re-scraped and reappearing on the next run.

**Status bars.** The dark blue bar reports scraping progress while a run is
active. The yellow bar below it reports how many new jobs have been found since
the page was loaded, and reloads the page when clicked. The page never reloads
on its own, so your scroll position and selections are preserved during a run.

**Job storage.** Processed jobs are stored in the local SQLite database at
`data/jobs.db`. The digest shows all stored jobs above your match threshold, not
only jobs from the most recent run, so results accumulate across runs until
deleted.

## Requirements

- macOS
- Python 3.10 or newer
- [Ollama](https://ollama.com/download)
- The Ollama model `gemma4:e4b`, or another compatible locally installed model
- Chromium for Playwright

## Reed API Key

Searching Reed requires a Reed account and an API key. Register with Reed,
request or obtain an API key, and then save it as the `REED_API_KEY`
environment variable before starting Job Agent.

Replace `your-key-here` with your actual Reed API key and run:

```bash
echo 'export REED_API_KEY=your-key-here' >> ~/.zshrc
source ~/.zshrc
```

This makes the key available in the current terminal and future zsh sessions.
Do not add the real key to this repository or commit it to Git.

If the key is not set, Reed logs a notice and returns no results. Every other
board continues to run normally.

## Quick Start

Install Ollama and start it in a separate terminal:

```bash
ollama serve
```

If Ollama reports that the address is already in use, it is probably already
running.

Clone and set up this fork:

```bash
git clone <this-repository-url>
cd job_agent

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium

ollama pull gemma4:e4b
```

Create your configuration file and run:

```bash
cp data/user_config.example.json data/user_config.json
python main.py --run
```

Edit `data/user_config.json` with your roles, locations, keywords, filters, and
`cv_text` before the first real run. The virtual environment must be active in
every new terminal session:

```bash
source venv/bin/activate
```

## Configure Your Search

This fork is configured through the file `data/user_config.json`, which is read
by `python main.py --run`.

> **Note on the settings page.** The browser settings form at
> `http://localhost:8765/settings` is inherited from the original project. Its
> Job Boards checkboxes list only LinkedIn, Stepstone, and Xing, and it cannot
> set any of the filter options added in this fork. Reed, Job Bank, Himalayas,
> the PhD filter, topic exclusions, and the salary floor are only available
> through `data/user_config.json`. Use the file-based run for this fork.

### Core options

- **`roles`** — target job titles, one per entry. These serve two purposes: they
  are the search queries sent to every board, and a job's title must contain one
  of them to be considered. Shorter base terms such as `Data Scientist` match
  more broadly than long phrases such as `Senior Research Data Scientist`. Order
  matters, because each board stops at its job cap and later roles may never be
  searched.
- **`description_keywords`** — skills, research areas, or phrases. A job whose
  description contains none of these is skipped before scoring. Leave the list
  empty to disable this check.
- **`locations`** — one location per entry. Used by LinkedIn, Stepstone, and
  Xing only.
- **`match_threshold`** — the minimum CV match score for a job to appear in the
  digest, for example `0.80`.
- **`enabled_scrapers`** — which boards to search, for example
  `["linkedin", "stepstone", "reed", "jobbank", "himalayas"]`. Defaults to
  LinkedIn, Stepstone, and Xing when absent.
- **`cv_text`** — your CV as plain text.

### Filter options added in this fork

- **`require_phd`** — when `true`, keeps only jobs whose description mentions a
  PhD or doctorate, whether stated as required, preferred, or advantageous.
  Defaults to `false`.

  Because Reed and Job Bank return shortened description snippets, a role that
  requires a PhD deeper in its full posting can be dropped by this filter.
  Enabling it will reduce results from those boards noticeably.

- **`phd_keywords`** — optional custom list of PhD terms, replacing the built-in
  defaults.

- **`exclude_focus`** — when `true`, applies the topic exclusions below.
  Defaults to `true`.

- **`exclude_keywords`** — lenient exclusions, intended for topics that are
  acceptable in passing but not as the job's focus. A job is removed only when
  the term appears in the **title**, or three or more times in the description.
  Default terms cover LLM, NLP, generative text, and computer-vision work. A
  single mention such as "we occasionally use LLMs" is not enough to remove a
  job, and phrases such as "medical imaging" are unaffected.

- **`hard_exclude_keywords`** — strict exclusions. A **single** mention anywhere
  in the title or description removes the job. Default terms cover military,
  defense, weapons, national security, and security-clearance requirements.
  These are treated as disqualifying rather than merely off-topic.

- **`min_salary`** — a minimum salary floor, compared as a raw number so it
  works across currencies. Handles formats such as `60,000`, `90.000`,
  `50 000`, `75k`, and `EUR 60000`.

  Jobs that state **no** salary always pass this filter. Most postings omit
  salary entirely, so rejecting them would discard the majority of real
  listings. A job is removed only when it states a figure and that figure is
  below the floor. Set to `0` to disable.

### Job cap per board

`main.py` defines `MAX_JOBS_PER_SOURCE`, which limits how many listings each
board returns per run. The cap applies to the whole board, not per role, so if
your first role fills the cap, later roles are not searched at all. Raise it for
broader coverage at the cost of longer runs.

## Ollama Model

The app reads the model name from the `OLLAMA_MODEL` environment variable. If
the variable is not set, it uses:

```text
gemma4:e4b
```

Install the default model:

```bash
ollama pull gemma4:e4b
```

List the models installed on your machine:

```bash
ollama list
```

Use a different installed model for one run:

```bash
OLLAMA_MODEL=<model-name> python main.py --run
```

The model name must exactly match one shown by `ollama list`.

## Test Mode

Test the Python environment, Ollama connection, and local digest server without
scraping external job boards:

```bash
source venv/bin/activate
python main.py --run --test
```

Test mode uses mock jobs, but Ollama must still be running and the configured
model must be installed. Mock jobs are written to the database like any other
job; delete them from the digest once the test passes.

## Browser Settings Mode

Running `python main.py` without `--run` starts the original browser-configured
mode, which stores its settings separately from `data/user_config.json`. As
noted above, that mode cannot reach the boards or filters added in this fork.
It is retained for compatibility only.

## Optional macOS Login Startup

The `com.jobagent.plist` file is a launchd template that can start the browser
app when you log in.

1. Replace every `/Users/YOUR_USERNAME/job_agent` path in
   `com.jobagent.plist` with the correct local path.
2. Copy the file to `~/Library/LaunchAgents/`.
3. Load it with `launchctl`.

```bash
cp com.jobagent.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.jobagent.plist
```

To stop it later:

```bash
launchctl unload ~/Library/LaunchAgents/com.jobagent.plist
```

Manual startup with `python main.py --run` is recommended until the app has been
tested successfully.

## Project Structure

```text
job_agent/
|-- main.py                     # Application entry point and filter pipeline
|-- requirements.txt            # Python dependencies
|-- com.jobagent.plist          # Optional macOS launchd template
|-- data/
|   `-- user_config.example.json
|-- core/
|   |-- agent.py                # Ollama scoring and resume tailoring
|   |-- cv_parser.py            # PDF CV text extraction
|   |-- db.py                   # SQLite job cache, viewed and deleted flags
|   |-- emailer.py              # Browser digest HTML builder
|   |-- filters.py              # Title, keyword, PhD, exclusion, salary filters
|   |-- resume_data.py          # Empty fallback resume placeholders
|   |-- server.py               # Local settings and digest server
|   `-- user_config.py          # File-based configuration loader
|-- scrapers/
|   |-- common.py               # Shared scraper helpers
|   |-- linkedin.py
|   |-- stepstone.py
|   |-- xing.py
|   |-- reed.py                 # Reed Jobseeker API
|   |-- jobbank.py              # Canada Job Bank RSS, international candidates
|   `-- himalayas.py            # Himalayas public JSON API
`-- output/
    `-- digests/
```

## Private and Generated Files

The following local files should remain outside the public repository:

- `venv/` and `.venv/`
- Python cache directories
- Local assistant or editor folders
- `data/jobs.db`
- `data/user_config.json`
- Generated files under `output/`
- CV and resume files

Use `data/user_config.example.json` as the tracked configuration example. Never
commit a CV, a configuration file containing personal information, or a Reed API
key.

## Troubleshooting

### `ModuleNotFoundError: No module named 'ollama'`

Activate the virtual environment and reinstall the dependencies:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### `playwright not installed` or Scrapers Return Zero Listings

Usually the virtual environment is not active in the current terminal. Each new
terminal session needs:

```bash
source venv/bin/activate
```

### Ollama Is Not Responding

Start Ollama, then restart Job Agent:

```bash
ollama serve
```

### Configuration Changes Have No Effect

Check the `Loaded config:` line printed at startup. If it reports
`roles=[], cv_text_len=0`, the configuration file failed to parse and defaults
were used. The most common causes are curly quotes pasted from a word processor
instead of straight quotes, and Python-style `True` or `False` instead of JSON's
lowercase `true` and `false`.

Validate the file directly:

```bash
python3 -c "import json; json.load(open('data/user_config.json')); print('valid')"
```

### No Jobs Appear

Filters are cumulative, and each one runs before scoring. Check in this order:

- **Match threshold** — `0.80` is strict. Try `0.70`.
- **Salary floor** — removes jobs that state a figure below `min_salary`.
- **Topic exclusions** — `hard_exclude_keywords` removes a job on a single
  mention, which can be broader than expected.
- **PhD filter** — if `require_phd` is `true`, expect far fewer results from
  Reed and Job Bank, which return short description snippets.
- **Roles** — long multi-word titles match fewer postings than short ones.
- **Job cap** — `MAX_JOBS_PER_SOURCE` may be exhausted by your first role before
  later roles are searched.

Also confirm that the selected sources currently contain listings for your roles
and locations, and that the external job board has not changed its page
structure.

### Old Jobs Keep Appearing

The digest shows every stored job above the threshold, not only jobs from the
latest run. Select unwanted jobs and use **Delete selected**, or clear the
database:

```bash
sqlite3 data/jobs.db "DELETE FROM seen_jobs;"
```

## Acknowledgements

This project is based on the original **Job Agent** repository by
**maralsage**. This fork adds new job sources, custom PhD-focused and
topic-based filtering, and an extended digest interface for a more specialized
search workflow.
