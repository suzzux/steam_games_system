from src.ports.dtos import GameFilterDTO, GameCreateCommandDTO


def test_ingest_writes_documents_and_counters(system):
    assert system["report"].saved == 5
    doc = system["client"]["steam"]["games"].find_one({"_id": 81506})
    assert doc["name"] == "FALLEN ANGELS" and doc["game_designers"] == ["Jacob Davis"]
    assert system["cache"].counters["stats:generator:saved"] == 5


def test_reload_is_idempotent(system):
    from tests.sample_data import commands
    system["cmd"].ingest_many(commands())
    assert system["client"]["steam"]["games"].count_documents({}) == 5


def test_list_with_filters_and_sort(system):
    page = system["qry"].list_games(GameFilterDTO(genre="Indie", sort="price_desc"))
    assert [g.game_id for g in page.items] == [1117, 95184, 19338, 192662]
    assert page.total == 4
    page = system["qry"].list_games(GameFilterDTO(platform="PC", year_from=2016, year_to=2020))
    assert [g.game_id for g in page.items] == [95184]
    page = system["qry"].list_games(GameFilterDTO(name_prefix="cap"))
    assert [g.name for g in page.items] == ["Captain Forever Remix"]


def test_pagination(system):
    page = system["qry"].list_games(GameFilterDTO(page=2, page_size=2, sort="name_asc"))
    assert page.pages == 3 and len(page.items) == 2


def test_details_and_facets(system):
    card = system["qry"].get_details(19338)
    assert card.positive_ratio == round(5000 / 5900, 3) and card.engine == "UbiArt Framework"
    facets = system["qry"].get_facets()
    assert "Wii U" in facets.platforms and "Sci-Fi" in facets.genres


def test_search_uses_cache_on_second_call(system):
    first = system["qry"].search_games("Space shooter")
    second = system["qry"].search_games("shooter   SPACE")
    assert first.source == "elasticsearch" and second.source == "redis"
    assert [g.game_id for g in first.items] == [g.game_id for g in second.items] == [1117, 81506]
    assert system["search"].calls == 1


def test_filter_by_relations(system):
    result = system["qry"].filter_by_relations("Wii U", "Jacob Davis")
    assert [g.game_id for g in result.items] == [81506] and result.source == "neo4j"
    assert system["qry"].filter_by_relations("Wii U", "Jacob Davis").source == "redis"


def test_create_update_delete_flow(system):
    cmd = GameCreateCommandDTO(name="New Game", price=1.5, min_age=0, release_date="2026-11-01",
                               short_description="s", detailed_description="d", engine="Godot",
                               genres=["Indie"], platforms=["PC"], designers=["Me"])
    new_id = system["cmd"].ingest_game(cmd)
    assert new_id == 192663
    cmd.game_id, cmd.price = new_id, 2.5
    system["cmd"].update_game(cmd)
    assert system["repo"].find_by_id(new_id).price.amount == 2.5
    assert system["cmd"].delete_game(new_id) is True
    assert system["publisher"].events[-1] == ("game.deleted", new_id)


def test_sync_removes_deleted_games(system):
    system["repo"].delete_by_id(95184)
    system["sync"].sync_games([95184])
    assert 95184 not in system["search"].docs and 95184 not in system["graph"].games


def test_invalid_rows_are_skipped(system):
    bad = GameCreateCommandDTO(game_id=5, name="", price=-3, min_age=0, release_date="", short_description="",
                               detailed_description="", engine="")
    report = system["cmd"].ingest_many([bad])
    assert report.failed == 1 and report.saved == 0
