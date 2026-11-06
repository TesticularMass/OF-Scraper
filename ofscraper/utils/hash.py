import io
import logging
import pathlib

import xxhash

import ofscraper.classes.placeholder as placeholder
import ofscraper.utils.of_env.of_env as of_env
import ofscraper.utils.settings as settings
from ofscraper.db.operations_.media import get_dupe_media_files, get_dupe_media_hashes

log = logging.getLogger("shared")


_fileHashes = {}


def get_hash(
    file_data,
):
    hash = None
    if settings.get_settings().hash is None:
        return
    if isinstance(file_data, placeholder.Placeholders):
        file_data = file_data.trunicated_filepath
    if _fileHashes.get(str(file_data)):
        hash = _fileHashes.get(str(file_data))
    else:
        hash = _calc_hash(file_data)
    log.debug(f"{file_data} => hash: {hash}")
    return hash


def invalidate_hash(file_path):
    """Remove a cached hash entry when the underlying file changes."""
    _fileHashes.pop(str(file_path), None)


def _calc_hash(file_data):
    hasher = xxhash.xxh128()
    BUF_SIZE = of_env.getattr("BUF_SIZE")
    with open(file_data, "rb") as f:
        buffered_f = io.BufferedReader(f, buffer_size=BUF_SIZE)
        for block in iter(lambda: buffered_f.read(BUF_SIZE), b""):
            hasher.update(block)
    _fileHashes[str(file_data)] = hasher.hexdigest()
    return hasher.hexdigest()


def remove_dupes_hash(username, model_id, mediatype=None):
    if not settings.get_settings().hash:
        return
    hashes = get_dupe_media_hashes(
        username=username, model_id=model_id, mediatype=mediatype
    )
    for hash in hashes:
        files = get_dupe_media_files(username=username, model_id=model_id, hash=hash)
        # Resolve paths so duplicates referring to the same inode are counted once
        seen_resolved = {}
        for f in files:
            p = pathlib.Path(f)
            if p.is_file():
                resolved = str(p.resolve())
                if resolved not in seen_resolved:
                    seen_resolved[resolved] = p
        unique_files = list(seen_resolved.values())
        if len(unique_files) < 2:
            continue
        # Keep the first copy, remove extras
        for p in unique_files[1:]:
            p.unlink(missing_ok=True)
            invalidate_hash(p)
