# Job Agent — PhD-Focused Fork

Job Agent is a local job-search assistant for macOS. It searches multiple job
boards, filters listings based on your preferred roles, locations, and job
requirements, scores matching jobs against your CV using a locally running
Ollama model, and displays the results in a browser digest.

This repository is a fork of the original **Job Agent** project by
**[maralsage](https://github.com/maralthesage)**, customized for a PhD-oriented job search.

## What Is New in This Fork

This fork extends the original project in three main ways:

- Added support for **Reed**.
- Added support for **Hymalia**.
- Added support for the **Government of Canada job portal**.
- Updated the filtering logic so that only jobs that list a **PhD as a
  requirement or as a preferred/advantageous qualification** are retained.
- Adjusted additional filter settings to better match a personalized job
  search, excluding specific job descriptions.

The original LinkedIn, Stepstone, and Xing sources remain part of the project,
alongside the newly added sources.

## How It Works

1. The selected job boards are searched for new listings.
2. Listings are checked against the configured roles, locations, keywords, and
   other filtering preferences.
3. The PhD filter removes jobs that do not mention a PhD as either required or
   desirable.
4. Ollama evaluates the remaining listings against your CV locally.
5. Jobs that meet the configured match threshold are shown in the browser
   digest.

Your CV and job data remain on your machine. No hosted language-model account
is required.

## Supported Job Boards

- LinkedIn
- Stepstone
- Xing
- Reed
- Hymalia
- Government of Canada job portal

Job-board availability and results can vary because external websites may
change their page structure or restrict automated access.

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
python main.py
```

When the browser opens, go to **Settings**, enter your search preferences, add
your CV, and select **Start Search**.

## Configure Your Search

Open the settings page at:

```text
http://localhost:8765/settings
```

Configure the available options:

- **Role Keywords:** one target job title per line, such as `Data Scientist` or
  `Research Scientist`.
- **Job Description Keywords:** optional skills, research areas, or phrases,
  such as `Python`, `machine learning`, or `bioinformatics`.
- **Locations:** one location per line, such as `London`, `Canada`, or `Remote`.
- **Match Threshold:** the minimum CV match score required for a job to appear
  in the digest, such as `0.75`.
- **Job Boards:** choose any supported job sources.
- **CV / Resume:** upload a PDF CV or paste the CV text.

The customized filters in this fork prioritize listings that explicitly state
that a PhD is required, preferred, desirable, or considered an advantage.
Review the filter configuration before running a search to ensure the role,
location, and keyword settings reflect your own needs.

After saving the settings, select **Start Search** and view results at:

```text
http://localhost:8765/digest
```

The digest updates while scraping and scoring are in progress. Processed jobs
are stored in the local SQLite database at `data/jobs.db`, preventing the same
listing from being processed repeatedly unless old jobs are cleared from the
settings page.

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
OLLAMA_MODEL=<model-name> python main.py
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
model must be installed.

## Optional File-Based Run

The browser interface is the simplest way to configure the app. For a
terminal-only run, create a local configuration file from the example:

```bash
cp data/user_config.example.json data/user_config.json
```

Edit `data/user_config.json` with your roles, locations, keywords, and
`cv_text`, then run:

```bash
python main.py --run
```

The `--run` command reads `data/user_config.json`; settings saved in the browser
are stored separately.

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

Manual startup with `python main.py` is recommended until the app has been
tested successfully.

## Project Structure

```text
job_agent/
|-- main.py                     # Application entry point
|-- requirements.txt            # Python dependencies
|-- com.jobagent.plist          # Optional macOS launchd template
|-- data/
|   `-- user_config.example.json
|-- core/
|   |-- agent.py                # Ollama scoring and resume tailoring
|   |-- cv_parser.py            # PDF CV text extraction
|   |-- db.py                   # SQLite job cache
|   |-- emailer.py              # Browser digest HTML builder
|   |-- filters.py              # PhD and personalized job filters
|   |-- resume_data.py          # Empty fallback resume placeholders
|   |-- server.py               # Local settings and digest server
|   `-- user_config.py          # File-based configuration loader
|-- scrapers/
|   |-- linkedin.py
|   |-- stepstone.py
|   |-- xing.py
|   |-- reed.py
|   |-- hymalia.py
|   `-- canada_government.py
`-- output/
    `-- digests/
```

The exact filenames of the added scrapers may differ depending on the current
implementation.

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
commit a CV or a configuration file containing personal information.

## Troubleshooting

### `ModuleNotFoundError: No module named 'ollama'`

Activate the virtual environment and reinstall the dependencies:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Ollama Is Not Responding

Start Ollama, then restart Job Agent:

```bash
ollama serve
```

### No Jobs Appear

Because this fork applies a PhD-specific filter, a search can legitimately
return fewer results than the original project. Check that:

- The selected sources currently contain listings for your chosen roles and
  locations.
- The listings explicitly mention a PhD as required or preferred.
- Your role, location, keyword, and match-threshold settings are not overly
  restrictive when combined.
- The external job board has not changed its page structure.

## Acknowledgements

This project is based on the original **Job Agent** repository by
**maralsage**. This fork adds new job sources and custom PhD-focused filtering
for a more specialized search workflow.
