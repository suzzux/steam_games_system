from typing import List

from src.ports.outbound import FullTextSearchPort
from src.domain.entities import Game

INDEX = "games_search"

# Налаштування індексу: 2 первинні шарди, англійський аналізатор (стемінг: shooting -> shoot),
# окреме поле name_suggest типу search_as_you_type для автодоповнення назви.
INDEX_SETTINGS = {"number_of_shards": 2, "number_of_replicas": 0}
INDEX_MAPPINGS = {
    "properties": {
        "game_id": {"type": "long"},
        "name": {"type": "text", "analyzer": "english", "fields": {"raw": {"type": "keyword"}}},
        "name_suggest": {"type": "search_as_you_type"},
        "detailed_description": {"type": "text", "analyzer": "english"},
        "reviews": {"type": "text", "analyzer": "english"},
    }
}


def game_to_search_doc(game: Game) -> dict:
    """В Elasticsearch потрапляють лише поля для пошуку (розділ 1.4.2)."""
    return {"game_id": game.game_id, "name": game.name, "name_suggest": game.name,
            "detailed_description": game.detailed_description, "reviews": game.reviews}


class ElasticAdapter(FullTextSearchPort):

    def __init__(self, client, index: str = INDEX, replicas: int = 0):
        self.es = client
        self.index = index
        self.replicas = replicas

    def ensure_index(self) -> None:
        if not self.es.indices.exists(index=self.index):
            settings = dict(INDEX_SETTINGS, number_of_replicas=self.replicas)
            self.es.indices.create(index=self.index, settings=settings, mappings=INDEX_MAPPINGS)

    def index_games(self, games: List[Game]) -> int:
        from elasticsearch import helpers
        actions = ({"_op_type": "index", "_index": self.index, "_id": g.game_id, "_source": game_to_search_doc(g)}
                   for g in games)                       # _id = game_id: повторна індексація перезаписує документ
        ok, _ = helpers.bulk(self.es, actions, raise_on_error=False)
        return ok

    def delete_games(self, game_ids: List[int]) -> None:
        from elasticsearch import helpers
        actions = ({"_op_type": "delete", "_index": self.index, "_id": i} for i in game_ids)
        helpers.bulk(self.es, actions, raise_on_error=False)

    def search_by_text(self, text_query: str, limit: int = 50) -> List[int]:
        response = self.es.search(
            index=self.index,
            size=limit,
            source=False,
            query={"multi_match": {
                "query": text_query,
                "fields": ["name^3", "detailed_description", "reviews"],   # збіг у назві важить утричі більше
                "fuzziness": "AUTO",                                        # допускаємо дрібні описки
            }},
        )
        return [int(hit["_id"]) for hit in response["hits"]["hits"]]       # порядок за релевантністю (BM25)

    def autocomplete(self, prefix: str, limit: int = 8) -> List[str]:
        response = self.es.search(
            index=self.index,
            size=limit,
            source=["name"],
            query={"multi_match": {
                "query": prefix,
                "type": "bool_prefix",
                "fields": ["name_suggest", "name_suggest._2gram", "name_suggest._3gram"],
            }},
        )
        return [hit["_source"]["name"] for hit in response["hits"]["hits"]]
