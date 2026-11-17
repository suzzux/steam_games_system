import csv

from src.adapters.driving.dataset_loader import DatasetLoader, parse_list, row_to_command
from src.adapters.driving.kafka_consumer import split_events
from src.adapters.driven.neo4j_adapter import game_to_row
from src.services.mappers import command_to_game


def test_parse_list_formats():
    assert parse_list("['Action', 'Indie']") == ["Action", "Indie"]
    assert parse_list("Action,Indie") == ["Action", "Indie"]
    assert parse_list("[]") == [] and parse_list("") == []


def test_loader_reads_csv(tmp_path, system):
    path = tmp_path / "games.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["appID", "name", "release_date", "price", "required_age", "genres", "platforms",
                    "game_designers", "engine", "positive", "negative"])
        w.writerow([10, "Half-Life", "Nov 8, 1998", "9.99", "0", "['Action']", "['PC']", "['Gabe']", "GoldSrc", 5, 1])
        w.writerow(["oops", "Broken", "", "1", "0", "[]", "[]", "[]", "", 0, 0])
    report = DatasetLoader(system["cmd"], batch_size=1).load(str(path))
    assert (report.processed, report.saved, report.failed) == (2, 1, 1)
    assert system["repo"].find_by_id(10).release_date.date_str == "1998-11-08"


def test_last_event_wins():
    events = [{"type": "game.upserted", "game_id": 1}, {"type": "game.deleted", "game_id": 1},
              {"type": "game.upserted", "game_id": 2}]
    assert split_events(events) == ([2], [1])


def test_neo4j_row_has_no_empty_engine():
    cmd = row_to_command({"appID": "7", "name": "X", "engine": ""})
    assert game_to_row(command_to_game(cmd, 7))["engines"] == []
