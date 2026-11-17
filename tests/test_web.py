"""Повний флоу через HTTP: браузер -> FastAPI -> контролер -> сервіс -> репозиторій -> MongoDB (mongomock)."""
from fastapi.testclient import TestClient

from src.adapters.driving.api_controller import GameAPIController
from src.adapters.driving.web.app import create_app
from src.services.analytics_service import MonitoringService


def make_client(system):
    controller = GameAPIController(
        command_port=system["cmd"], update_port=system["cmd"], delete_port=system["cmd"],
        list_port=system["qry"], details_port=system["qry"], search_port=system["qry"],
        filter_port=system["qry"], monitoring_port=MonitoringService(system["cache"]))
    return TestClient(create_app(controller))


def test_catalog_page(system):
    client = make_client(system)
    html = client.get("/games?genre=Indie&sort=price_desc").text
    assert "Captain Forever Remix" in html and "FALLEN ANGELS" not in html
    assert "Знайдено записів: 4" in html


def test_game_card_and_404(system):
    client = make_client(system)
    assert "UbiArt Framework" in client.get("/games/19338").text
    assert client.get("/games/424242").status_code == 404


def test_create_via_form(system):
    client = make_client(system)
    r = client.post("/games/new", data={"name": "Form Game", "price": "3", "min_age": "0",
                                        "genres": "Indie, Puzzle", "platforms": "PC"}, follow_redirects=False)
    assert r.status_code == 303
    game_id = int(r.headers["location"].rsplit("/", 1)[1])
    assert system["repo"].find_by_id(game_id).genres[1].name == "Puzzle"


def test_search_and_filter_pages(system):
    client = make_client(system)
    assert "Captain Forever Remix" in client.get("/search?q=space shooter").text
    assert "кеш Redis" in client.get("/search?q=space shooter").text
    assert "FALLEN ANGELS" in client.get("/filter?platform=Wii U&designer=Jacob Davis").text


def test_json_api(system):
    client = make_client(system)
    data = client.get("/api/games", params={"platform": "PS5", "sort": "name_asc"}).json()
    assert [g["name"] for g in data["items"]] == ["Captain Forever Remix", "Patterna Environmental: Situation",
                                                  "Rebound VR"]
    assert client.get("/api/games/1117").json()["engine"] == "Unity"
    assert client.post("/api/games", json={"name": "", "price": 1, "min_age": 0, "release_date": "",
                                           "short_description": "", "detailed_description": "",
                                           "engine": ""}).status_code == 400
    assert client.get("/monitoring").status_code == 200


def test_shards_and_analytics_pages(system):
    from src.ports.dtos import ShardDistributionDTO
    from src.services.analytics_service import ShardAnalyticsService
    from tests.test_map_reduce import make_cluster

    adapter = make_cluster()
    adapter.shard_distribution = lambda: [ShardDistributionDTO("rs-shard1", 3, 1.2, 4),
                                          ShardDistributionDTO("rs-shard2", 2, 0.8, 4)]
    controller = GameAPIController(
        command_port=system["cmd"], update_port=system["cmd"], delete_port=system["cmd"],
        list_port=system["qry"], details_port=system["qry"], search_port=system["qry"],
        filter_port=system["qry"], analytics_port=ShardAnalyticsService(adapter))
    client = TestClient(create_app(controller))
    assert "60.0%" in client.get("/shards").text
    html = client.get("/analytics?run=1&group_by=platforms&top_n=5").text
    assert "збігається" in html and "Xbox Series X/S" in html and "rs-shard2" in html
    assert client.get("/api/analytics/map-reduce?group_by=bad").status_code == 400
