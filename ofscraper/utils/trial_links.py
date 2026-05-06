import html
import logging
import re
from datetime import datetime
from pathlib import Path

import ofscraper.utils.paths.common as common_paths

log = logging.getLogger("shared")

TRIAL_LINK_RE = re.compile(
    r"https://onlyfans\.com/[^/\s\"'<>]+/trial/[A-Za-z0-9_-]+"
)

_seen_links: set[str] = set()


def reset():
    _seen_links.clear()


def scan_posts(posts, model_username):
    """Scan a batch of posts/messages for OF trial links and log findings."""
    for post in posts:
        text = _get_text(post)
        if not text:
            continue
        for match in TRIAL_LINK_RE.finditer(text):
            link = match.group(0)
            dedup_key = f"{model_username}:{link}"
            if dedup_key in _seen_links:
                continue
            _seen_links.add(dedup_key)
            _log_find(model_username, link, post, text)


def _get_text(post) -> str:
    raw = getattr(post, "_post", None)
    if isinstance(raw, dict):
        text = raw.get("text")
        if text:
            return text
    try:
        return post.text or ""
    except Exception:
        return ""


def _get_post_date(post) -> str:
    raw = getattr(post, "_post", None)
    created_at = None
    if isinstance(raw, dict):
        created_at = raw.get("createdAt") or raw.get("postedAt") or raw.get("changedAt")
    if not created_at:
        try:
            created_at = getattr(post, "date", None)
        except Exception:
            pass
    if not created_at:
        return ""
    try:
        if isinstance(created_at, (int, float)):
            return datetime.fromtimestamp(created_at).strftime("%Y-%m-%d %H:%M")
        if isinstance(created_at, str):
            clean = created_at.rstrip("Z").split("+")[0].split(".")[0]
            return datetime.fromisoformat(clean).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(created_at)[:16]
    return ""


def _log_find(model_username: str, link: str, post, text: str):
    date_str = _get_post_date(post)
    log.info(f"Trial link found — {model_username}: {link}")
    _write_log_file(model_username, link, date_str, text)


def _write_log_file(model: str, link: str, date_str: str, text: str):
    try:
        log_dir = common_paths.get_log_folder() / "trial_links"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"trial_links_{datetime.now().strftime('%Y-%m-%d')}.log"
        timestamp = datetime.now().isoformat(timespec="seconds")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] model={model} date={date_str} link={link}\n")
            cleaned = _strip_html(text)
            if cleaned:
                indented = "\n".join("    " + line for line in cleaned.splitlines())
                f.write(indented + "\n")
            f.write("\n")
    except Exception as e:
        log.warning(f"Failed to write trial link log: {e}")


def _strip_html(text: str) -> str:
    cleaned = re.sub(r"<[^>]+>", "", text)
    return html.unescape(cleaned).strip()
