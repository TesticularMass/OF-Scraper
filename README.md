# OF-Scraper

A command-line tool for downloading media from OnlyFans and performing bulk actions like liking, unliking, and subscribing.

> I found something useful and wanted to make it better. That's it.

![Python](https://img.shields.io/badge/python-3.11%E2%80%933.14-blue.svg)
![License](https://img.shields.io/badge/license-GPL--3.0-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)

## Features

### Core Features
- **Media Download** — Photos, videos, and audio from subscribed models
- **Bulk Like/Unlike** — Toggle likes across multiple models and posts at configurable rates
- **Subscribe Action** — Batch-subscribe to expired accounts that are free or have a claimable $0 promo
- **Interactive Table UI** — Terminal-based table with filtering, sorting, and per-row download cart
- **Content Areas** — Timeline, Pinned, Archived, Labels, Streams, Messages, Stories, Highlights, and Purchased content
- **DRM Support** — Handles DRM-protected content with proper CDM setup
- **Daemon Mode** — Automated recurring scrapes on a configurable interval

### Data Management
- **Deduplication** — Local SQLite databases track downloaded content, skip duplicates
- **Database Table** — Inspect scraped post/media info straight from the local database
- **Caching** — API responses cached to avoid redundant network calls

### Filtering & Sorting
- **Model Filters** — Filter subscriptions by active/expired status, price, last seen, promo availability, and more
- **Media Filters** — Filter by media type, quality, duration, file size, download status
- **Sort Options** — Sort models and media by date, price, username, type, and more

### Trial Link Scanner
- **Message Scanning** — Scan message and paid-post text for OnlyFans trial links
- **Deduplicated Logging** — Daily log files with timestamps, model names, and cleaned post text
- **Subscription Filtering** — Target all subscriptions or filter by active/inactive status

## Important

1. This tool cannot bypass paywalls
2. A valid subscription to each model is required — anonymous scraping is not supported

## Installation

### Requirements
- Python 3.11–3.14
- ffmpeg (for video processing and DRM decryption)

### Setup

```bash
git clone https://github.com/TesticularMass/OF-Scraper.git
cd OF-Scraper
pip install -r requirements.txt
pip install -e . --no-build-isolation

# Run (interactive menu)
ofscraper
```

## Usage

Run `ofscraper` with no arguments for the interactive menu, or drive everything with flags:

### Main Scraper Mode

```bash
# Download media from all subscriptions
ofscraper --action download --username ALL

# Download from specific users
ofscraper --action download --username model1,model2

# Only active subscriptions
ofscraper --action download --username ALL --active-subscription

# Restrict content areas
ofscraper --action download --username model1 --posts Timeline Archived Messages

# Download text only (skip media)
ofscraper --action download --username model1 --text-only

# Bulk like posts from a model
ofscraper --action like --username model1

# Bulk unlike previously liked posts
ofscraper --action unlike --username model1

# Subscribe to all eligible free/$0-promo expired accounts
ofscraper --action subscribe --username ALL

# Subscribe then download in one run
ofscraper --action subscribe,download --username model1

# Daemon mode — re-run every 60 minutes
ofscraper --action download --username ALL --daemon 60

# Force redownload of all media
ofscraper --action download --username model1 --force-all
```

### Check Modes (Interactive Table)

Browse content in the terminal table without committing to a full scrape:

```bash
# Check messages for specific models
ofscraper msg_check --username model1

# Check posts/timeline
ofscraper post_check --username model1

# Check paid content
ofscraper paid_check --username model1,model2

# Check stories and highlights
ofscraper story_check --username model1

# Force fresh data from the API instead of cache
ofscraper post_check --username model1 --force
```

### Trial Link Scanner

```bash
# Scan all active subscriptions for trial links
ofscraper msg_check --username ALL --subscription-status active --scan-trial-links

# Scan specific user's paid content
ofscraper paid_check --username modelName --scan-trial-links

# Scan all expired subscriptions
ofscraper msg_check --username ALL --subscription-status inactive --scan-trial-links

# Only report links from posts on or after a date
ofscraper msg_check --username ALL --scan-trial-links --trial-min-date 2026-01-01
```

Trial links are written to `{log_folder}/trial_links/trial_links_{YYYY-MM-DD}.log`.

### Metadata Mode

```bash
# Scrape metadata for all subscriptions without downloading media
ofscraper metadata --username ALL

# Include paid content info
ofscraper metadata --username model1 --scrape-paid

# Anonymous metadata scrape (requires specific usernames)
ofscraper metadata --username model1 --anon
```

### Database Table

```bash
# Print scraped post/media info from the local database
ofscraper db --username model1 --posts messages
```

Database merge and transition tools are available through the interactive menu (`ofscraper` with no arguments).

## Architecture

```
.
├── ofscraper/
│   ├── commands/               # CLI command implementations
│   │   ├── check.py            # Check modes (msg/post/paid/story)
│   │   ├── scraper/            # Scraper actions (download, like, unlike, subscribe)
│   │   ├── metadata/           # Metadata operations
│   │   └── db.py               # Database table command
│   ├── classes/
│   │   ├── of/                 # OF data models (Post, Media, Model)
│   │   └── table/              # Terminal table UI
│   ├── data/
│   │   ├── api/                # API clients (timeline, messages, paid, subscriptions, etc.)
│   │   ├── models/             # Model retriever utilities
│   │   └── posts/              # Post processing
│   ├── db/                     # Database layer (SQLite, schema, operations)
│   ├── filters/                # Model and media filtering
│   ├── managers/               # Session, model, and state managers
│   ├── scripts/                # User script hooks (naming, after-download, skip)
│   ├── utils/
│   │   ├── args/               # CLI argument parsing (Click/Cloup)
│   │   ├── auth/               # Authentication and header management
│   │   └── trial_links.py      # Trial link scanner
│   └── prompts/                # Interactive terminal prompts
```

## Docker

A `Dockerfile` is included for containerized runs:

```bash
# Build the image
docker build -t ofscraper .

# Run with mounted config
docker run -it -v ~/.config/ofscraper:/root/.config/ofscraper ofscraper
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Disclaimer

This tool is not affiliated with, endorsed by, or sponsored by OnlyFans. All OnlyFans trademarks remain the property of Fenix International Limited. This software is provided as-is for educational purposes. Use at your own risk.
