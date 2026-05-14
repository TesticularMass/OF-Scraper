import logging
import re
import arrow

import ofscraper.utils.paths.common as common_paths

log = logging.getLogger("shared")

TRIAL_LINK_RE = re.compile(
    r"https://onlyfans\.com/[^/\s\"'<>]+/trial/[A-Za-z0-9_-]+"
)

_seen_links: set[str] = set()


def reset():
    _seen_links.clear()


def count():
    return len(_seen_links)


def scan_posts(posts, model_username, min_date=None):
    """Scan a batch of posts/messages for OF trial links and log findings."""
    new_findings = []

    for post in posts:
        # Use Post object properties directly
        text = post.text or post.db_sanitized_text
        if not text:
            continue

        post_date_obj = arrow.get(post.date) if post.date else None

        if min_date and post_date_obj:
            if post_date_obj < min_date:
                continue

        for match in TRIAL_LINK_RE.finditer(text):
            link = match.group(0)
            dedup_key = f"{model_username}:{link}"
            
            if dedup_key in _seen_links:
                continue
                
            _seen_links.add(dedup_key)
            date_str = post_date_obj.format("YYYY-MM-DD HH:mm") if post_date_obj else ""
            
            # Log to console immediately
            date_part = f" [{date_str}]" if date_str else ""
            log.info(f"Trial link found — {model_username}{date_part}: {link}")
            
            # Queue for batch file write
            new_findings.append((model_username, link, date_str))

    if new_findings:
        _write_log_file_batch(new_findings)


def _write_log_file_batch(findings: list[tuple[str, str, str]]):
    try:
        log_dir = common_paths.get_log_folder() / "trial_links"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"trial_links_{arrow.now().format('YYYY-MM-DD')}.log"
        
        with open(log_path, "a", encoding="utf-8") as f:
            for model, link, date_str in findings:
                date_part = f" date={date_str}" if date_str else ""
                f.write(f"{link} poster={model}{date_part}\n")
                
    except Exception as e:
        log.warning(f"Failed to write trial link log batch: {e}")
