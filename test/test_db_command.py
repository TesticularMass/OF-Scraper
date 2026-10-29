import csv
from types import SimpleNamespace as NS

import ofscraper.commands.db as db_command


def test_db_exports_every_selected_model_to_one_file(monkeypatch, tmp_path):
    selected = [NS(name="first", id=1), NS(name="second", id=2)]
    monkeypatch.setattr(db_command.actions, "select_areas", lambda: None)
    monkeypatch.setattr(
        db_command.manager,
        "Manager",
        NS(current_model_manager=NS(prepare_scraper_activity=lambda: selected)),
    )
    monkeypatch.setattr(db_command.settings, "get_settings", lambda: NS(export=tmp_path / "out"))

    def print_media(self):
        self.media = [{"media_id": self.model_id * 10, "model_id": self.model_id}]

    monkeypatch.setattr(db_command.DBManager, "print_media", print_media)

    db_command.db()

    with open(tmp_path / "out.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    assert [row["model_id"] for row in rows] == ["1", "2"]
