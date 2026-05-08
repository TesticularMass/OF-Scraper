# OF-Scraper

A command-line tool for downloading media from OnlyFans and performing bulk actions like liking or unliking posts.

> I found something useful and wanted to make it better. That's it.

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![License](https://img.shields.io/badge/license-GPL--3.0-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)

## Features

### Core Features
- **Media Download** — Photos, videos, and audio from subscribed models
- **Bulk Like/Unlike** — Toggle likes across multiple models and posts at configurable rates
- **Interactive Table UI** — Terminal-based table with filtering, sorting, and per-row download cart
- **Content Areas** — Timeline, Pinned, Archived, Labels, Streams, Messages, and Purchased content
- **DRM Support** — Handles DRM-protected content with proper CDM setup
- **Daemon Mode** — Automated recurring scrapes on configurable intervals

### Data Management
- **Deduplication** — Local SQLite databases track downloaded content, skip duplicates
- **Database Operations** — Merge, export, and manage per-model databases
- **Caching** — API responses cached to avoid redundant network calls (override with `--force`)

### Filtering & Sorting
- **Model Filters** — Filter subscriptions by active/expired status, price, last seen, labels, and more
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
- Python 3.11+
- ffmpeg (for video processing)

### Setup

```bash
# Install from PyPI
pip install ofscraper

# Or clone and install locally
git clone https://github.com/TesticularMass/OF-Scraper.git
cd OF-Scraper
pip install -r requirements.txt

# Run
ofscraper
```

## Usage

### Main Scraper Mode

```bash
# Download media from all active subscriptions
ofscraper --usernames ALL --subscription-status active

# Download from specific users
ofscraper --usernames model1,model2

# Download text only (skip media)
ofscraper --usernames model1 --text-only

# Bulk like all posts from a model
ofscraper --usernames model1 --like

# Bulk unlike all liked posts
ofscraper --usernames model1 --unlike

# Daemon mode — re-scrape every 60 minutes
ofscraper --usernames ALL --daemon --daemon-delay 3600

# Force fresh data (skip cache)
ofscraper --usernames model1 --force
```

### Check Modes (Interactive Table)

```bash
# Check messages + paid content for a model
ofscraper msg_check -u https://onlyfans.com/modelName

# Check posts/timeline for a model
ofscraper post_check -u https://onlyfans.com/modelName

# Check paid content by username
ofscraper paid_check -u model1,model2

# Check stories and highlights
ofscraper story_check -u model1
```

### Trial Link Scanner

```bash
# Scan all active subscriptions for trial links
ofscraper msg_check --usernames ALL --subscription-status active --scan-trial-links

# Scan specific user's paid content
ofscraper paid_check -u modelName --scan-trial-links

# Scan all expired subscriptions
ofscraper msg_check --usernames all --subscription-status inactive --scan-trial-links

# Scan from a file of usernames
ofscraper msg_check -f users.txt --scan-trial-links

# Force fresh API data while scanning
ofscraper msg_check --usernames ALL --scan-trial-links --force
```

Trial links are written to `{log_folder}/trial_links/trial_links_{YYYY-MM-DD}.log`.

### Metadata Mode

```bash
# Scrape metadata for all active subscriptions
ofscraper metadata --usernames ALL --subscription-status active

# Scrape metadata and paid content info
ofscraper metadata --usernames model1 --scrape-paid

# Anonymous metadata scrape (requires specific usernames)
ofscraper metadata --usernames model1 --anon
```

### Database Operations

```bash
# Merge databases
ofscraper db merge

# Export database
ofscraper db export

# View database info
ofscraper db info
```

## Architecture

```
.
├── ofscraper/
│   ├── commands/               # CLI command implementations
│   │   ├── check.py            # Check modes (msg/post/paid/story)
│   │   ├── scraper/            # Scraper actions (download, like, unlike)
│   │   └── db.py               # Database operations
│   ├── classes/
│   │   ├── of/                 # OF data models (Post, Media, Model)
│   │   └── table/              # Terminal table UI
│   ├── data/
│   │   ├── api/                # API clients (timeline, messages, paid, etc.)
│   │   ├── models/             # Model retriever utilities
│   │   └── posts/              # Post processing
│   ├── db/                     # Database layer (SQLite, schema, operations)
│   ├── managers/               # Session, model, and state managers
│   ├── utils/
│   │   ├── args/               # CLI argument parsing (Click/Cloup)
│   │   ├── auth/               # Authentication and header management
│   │   └── trial_links.py      # Trial link scanner
│   └── prompts/                # Interactive terminal prompts
```

## Documentation

[Full documentation](https://of-scraper.gitbook.io/of-scraper)

## Docker

```bash
# Pull the image
docker pull datawhores/ofscraper

# Run with mounted config
docker run -v ~/.config/ofscraper:/root/.config/ofscraper datawhores/ofscraper
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Disclaimer

This tool is not affiliated with, endorsed by, or sponsored by OnlyFans. All OnlyFans trademarks remain the property of Fenix International Limited. This software is provided as-is for educational purposes. Use at your own risk.
