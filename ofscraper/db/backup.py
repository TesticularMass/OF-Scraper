r"""

 _______  _______         _______  _______  _______  _______  _______  _______  _______
(  ___  )(  ____ \       (  ____ \(  ____ \(  ____ )(  ___  )(  ____ )(  ____ \(  ____ )
| (   ) || (    \/       | (    \/| (    \/| (    )|| (   ) || (    )|| (    \/| (    )|
| |   | || (__     _____ | (_____ | |      | (____)|| (___) || (____)|| (__    | (____)|
| |   | ||  __)   (_____)(_____  )| |      |     __)|  ___  ||  _____)|  __)   |     __)
| |   | || (                   ) || |      | (\ (   | (   ) || (      | (      | (\ (
| (___) || )             /\____) || (____/\| ) \ \__| )   ( || )      | (____/\| ) \ \__
(_______)|/              \_______)(_______/|/   \__/|/     \||/       (_______/|/   \__/

"""

import logging
import os
import pathlib
import sqlite3
from contextlib import closing

import arrow
from rich.console import Console

import ofscraper.classes.placeholder as placeholder
import ofscraper.utils.cache.cache as cache
import ofscraper.utils.of_env.of_env as of_env
from ofscraper.db.difference import get_group_difference

console = Console()
log = logging.getLogger("shared")


def _connect(path):
    return sqlite3.connect(path, timeout=of_env.getattr("DATABASE_TIMEOUT"))


def _snapshot(source, destination):
    """Write a consistent, standalone copy of a live database.

    Copying the file misses commits still held in the WAL file, so the copy
    is read through SQLite instead.
    """
    source, destination = pathlib.Path(source), pathlib.Path(destination)
    if not source.is_file():
        raise FileNotFoundError(f"database not found: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(f"{destination.name}.partial")
    partial.unlink(missing_ok=True)
    with closing(_connect(source)) as src, closing(_connect(partial)) as dst:
        src.backup(dst)
        # The copy inherits WAL mode; a backup should be one self-contained file.
        dst.execute("PRAGMA journal_mode=DELETE")
    os.replace(partial, destination)


def restore_backup_transition(backup, model_id, username, db_path=None, **kwargs):
    if not backup:
        log.debug("no transition backup was made, nothing to restore")
        return
    database = db_path or placeholder.databasePlaceholder().databasePathHelper(
        model_id, username
    )
    # Writing through SQLite keeps open connections and the WAL file consistent;
    # replacing the file under them could pair it with a stale WAL.
    with closing(_connect(backup)) as src, closing(_connect(database)) as dst:
        src.backup(dst)
    log.debug(f"restored {database} from {backup}")


def create_backup_transition(model_id=None, username=None, db_path=None, **kwargs):

    if (
        len(get_group_difference(model_id=model_id, username=username, db_path=db_path))
        > 0
    ):
        log.info("creating a backup before transition")
        backup_name = (
            f"old_schema_{model_id}_{arrow.now().float_timestamp}_db_backup.db"
            if model_id
            else "old_schema_db_backup.db"
        )
        new_backup_path = create_backup(
            model_id, username, backup=backup_name, db_path=db_path
        )
        log.info(f"transition backup created at {new_backup_path}")
        check_backup(model_id, username, new_backup_path, db_path=db_path)
        return new_backup_path


def check_backup(model_id, username, new_path, db_path=None, **kwargs):
    new_path = pathlib.Path(new_path)
    if not new_path.is_file():
        raise Exception("Backup db was not created")
    # File sizes differ legitimately while the source has WAL pages, so check
    # that the backup itself is a sound database.
    with closing(_connect(new_path)) as conn:
        result = conn.execute("PRAGMA quick_check").fetchone()
    if not result or result[0] != "ok":
        raise Exception(f"backup db failed its integrity check: {result}")


def create_backup(model_id, username, backup=None, db_path=None, **kwargs):
    database_path = pathlib.Path(
        db_path
        or placeholder.databasePlaceholder().databasePathHelper(model_id, username)
    )
    database_copy = None
    if backup:
        database_copy = database_path.parent / "backup" / f"{backup}"
        _snapshot(database_path, database_copy)
        return database_copy

    now = arrow.now().float_timestamp
    last = cache.get(f"{username}_{model_id}_db_backup", default=now)
    backup_dir = database_path.parent / "backup"
    interval_passed = now - last > of_env.getattr("DBINTERVAL") and database_path.exists()
    no_backups_yet = not backup_dir.exists() or not any(backup_dir.iterdir())
    if interval_passed or no_backups_yet:
        database_copy = placeholder.databasePlaceholder().databasePathCopyHelper(
            model_id, username
        )
        _snapshot(database_path, database_copy)
        cache.set(f"{username}_{model_id}_db_backup", now)

    return database_copy
