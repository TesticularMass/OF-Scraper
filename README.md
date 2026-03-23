# OF-Scraper

A command-line and GUI tool for downloading media from OnlyFans and performing bulk actions like liking or unliking posts.

> I found something useful and wanted to make it better. That's it.

## What It Does

- Downloads photos, videos, and audio from OnlyFans subscriptions
- Bulk like/unlike posts across multiple models
- Scrapes content from Timeline, Messages, Stories, Highlights, Archived, Labels, and Paid content
- Handles DRM-protected content (with proper CDM setup)
- Deduplicates downloads using local SQLite databases
- Supports daemon mode for automated recurring scrapes
- Extensive filtering and sorting options for models and media
- Docker and binary releases available

## Important

1. This tool cannot bypass paywalls
2. A valid subscription to each model is required — anonymous scraping is not supported

## Installation

```bash
pip install ofscraper
```

Available via [PyPI](https://pypi.org/project/ofscraper/).

## Usage

```bash
# CLI mode
ofscraper

# GUI mode
ofscraper --gui
```

## GUI Mode

An optional graphical interface (built with tkinter) provides a visual alternative to the command line.

### Requirements

- Python 3.11–3.14
- tkinter (included with standard Python installations)

### What the GUI Provides

- **Action Selection** — Download, Like/Unlike, or both
- **Content Areas & Filters** — Select areas to scan and apply filters before scraping
- **Model Selection** — Searchable, sortable table of subscribed models with bulk select/deselect
- **Scraping Table** — Live view of scraped media with per-row download cart
- **Progress & Logs** — Real-time progress bar and scrollable console log
- **Authentication** — Built-in cookie/header editor for `auth.json`
- **Configuration** — Full `config.json` editor organized by category
- **Profile Management** — Create, switch, and delete profiles
- **Database Merge** — Merge multiple `user_data.db` files
- **Daemon Mode** — Auto-repeat scraping on a configurable interval
- **Theme Toggle** — Light and dark themes

## Documentation

[Full documentation](https://of-scraper.gitbook.io/of-scraper)

## Disclaimer

This tool is not affiliated with, endorsed by, or sponsored by OnlyFans. All OnlyFans trademarks remain the property of Fenix International Limited. This software is provided as-is for educational purposes. Use at your own risk.
