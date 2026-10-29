import sqlite3
from contextlib import closing

import pytest

from ofscraper.db import backup


@pytest.fixture(autouse=True)
def isolated_cache(monkeypatch):
    monkeypatch.setattr(backup.cache, "get", lambda *args, **kwargs: kwargs.get("default"))
    monkeypatch.setattr(backup.cache, "set", lambda *args, **kwargs: None)


def test_backup_includes_committed_wal_changes(tmp_path):
    db = tmp_path / "wal.db"
    with closing(sqlite3.connect(db)) as writer:
        writer.execute("PRAGMA journal_mode=WAL")
        writer.execute("CREATE TABLE data (value INTEGER)")
        writer.execute("INSERT INTO data VALUES (42)")
        writer.commit()
        # While the writer is open, the commit lives in the WAL file only.
        saved = backup.create_backup(1, "model", backup="snapshot.db", db_path=db)
        backup.check_backup(1, "model", saved, db_path=db)
    with closing(sqlite3.connect(saved)) as restored:
        assert restored.execute("SELECT value FROM data").fetchall() == [(42,)]


def test_restore_rewrites_a_database_that_is_still_open(tmp_path):
    db = tmp_path / "live.db"
    with closing(sqlite3.connect(db)) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("CREATE TABLE data (value INTEGER)")
        conn.execute("INSERT INTO data VALUES (1)")
        conn.commit()
        saved = backup.create_backup(1, "model", backup="before.db", db_path=db)
        conn.execute("INSERT INTO data VALUES (2)")
        conn.commit()
        backup.restore_backup_transition(saved, 1, "model", db_path=db)
        assert conn.execute("SELECT value FROM data").fetchall() == [(1,)]
