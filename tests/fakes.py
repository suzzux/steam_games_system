"""Фейкові адаптери в пам'яті: дозволяють перевірити сервіси й UI без запуску баз даних."""
from typing import Dict, List, Optional

from src.ports.outbound import FullTextSearchPort, GraphQueryPort, CachePort, EventPublisherPort


class FakeSearch(FullTextSearchPort):
    def __init__(self):
        self.docs: Dict[int, str] = {}
        self.calls = 0

    def index_games(self, games):
        for g in games:
            self.docs[g.game_id] = f"{g.name} {g.detailed_description} {g.reviews}".lower()
        return len(games)

    def delete_games(self, game_ids):
        for i in game_ids:
            self.docs.pop(i, None)

    def search_by_text(self, text_query, limit=50):
        self.calls += 1
        tokens = text_query.lower().split()
        return [i for i, text in sorted(self.docs.items()) if all(t in text for t in tokens)][:limit]

    def autocomplete(self, prefix, limit=8):
        return []


class FakeGraph(GraphQueryPort):
    def __init__(self):
        self.games: Dict[int, dict] = {}
        self.calls = 0

    def upsert_games(self, games):
        for g in games:
            self.games[g.game_id] = {"designers": {d.name for d in g.designers},
                                     "platforms": {p.name for p in g.platforms}}
        return len(games)

    def delete_games(self, game_ids):
        for i in game_ids:
            self.games.pop(i, None)

    def find_games_by_platform_and_designer(self, platform, designer, limit=100):
        self.calls += 1
        return [i for i, g in sorted(self.games.items()) if platform in g["platforms"] and designer in g["designers"]]


class FakeCache(CachePort):
    def __init__(self):
        self.data: Dict[str, object] = {}
        self.counters: Dict[str, int] = {}

    def get_search_cache(self, normalized_query) -> Optional[List[int]]:
        return self.data.get("search:query:" + normalized_query)

    def set_search_cache(self, normalized_query, game_ids, ttl):
        self.data["search:query:" + normalized_query] = list(game_ids)

    def get_filter_cache(self, platform, designer):
        return self.data.get(f"filter:{platform}:{designer}")

    def set_filter_cache(self, platform, designer, game_ids, ttl):
        self.data[f"filter:{platform}:{designer}"] = list(game_ids)

    def get_json(self, key):
        return self.data.get(key)

    def set_json(self, key, value, ttl):
        self.data[key] = value

    def increment(self, counter, amount=1):
        self.counters[counter] = self.counters.get(counter, 0) + amount
        return self.counters[counter]

    def get_counters(self):
        return dict(sorted(self.counters.items()))


class FakePublisher(EventPublisherPort):
    def __init__(self):
        self.events = []

    def publish_game_created_event(self, game_id):
        self.events.append(("game.upserted", game_id))

    def publish_game_deleted_event(self, game_id):
        self.events.append(("game.deleted", game_id))

    def flush(self):
        pass
