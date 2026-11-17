import logging
from typing import List

from src.ports.inbound import SyncGameProjectionPort
from src.ports.outbound import GameDocumentRepositoryPort, FullTextSearchPort, GraphQueryPort, CachePort

log = logging.getLogger(__name__)


class GameSyncService(SyncGameProjectionPort):
    """sync-worker: оновлює проєкції в Elasticsearch і Neo4j після подій з Kafka.

    Джерело істини - MongoDB, тому документ завжди перечитується з Primary
    (на Secondary він міг ще не з'явитися). Запис у проєкції ідемпотентний:
    в Elasticsearch за ключем game_id, у Neo4j через MERGE.
    """

    def __init__(self, document_repo: GameDocumentRepositoryPort, search: FullTextSearchPort,
                 graph_db: GraphQueryPort, cache: CachePort = None):
        self.document_repo = document_repo
        self.search = search
        self.graph_db = graph_db
        self.cache = cache

    def sync_games(self, game_ids: List[int]) -> int:
        unique_ids = list(dict.fromkeys(game_ids))
        if not unique_ids:
            return 0
        games = self.document_repo.find_by_ids(unique_ids, from_primary=True)
        found = {g.game_id for g in games}
        missing = [i for i in unique_ids if i not in found]
        if games:
            self.search.index_games(games)
            self.graph_db.upsert_games(games)
        if missing:                       # гру встигли видалити до обробки події
            self.remove_games(missing)
        if self.cache:
            self.cache.increment("stats:sync:processed", len(games))
        return len(games)

    def remove_games(self, game_ids: List[int]) -> int:
        if not game_ids:
            return 0
        self.search.delete_games(game_ids)
        self.graph_db.delete_games(game_ids)
        if self.cache:
            self.cache.increment("stats:sync:deleted", len(game_ids))
        return len(game_ids)
