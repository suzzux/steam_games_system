import re
from datetime import datetime
from typing import List, Optional, Tuple

from pymongo import ASCENDING, DESCENDING, ReplaceOne
from pymongo.errors import DuplicateKeyError
from pymongo.read_preferences import ReadPreference
from pymongo.write_concern import WriteConcern

from src.ports.outbound import GameDocumentRepositoryPort
from src.ports.dtos import GameFilterDTO
from src.domain.entities import Game
from src.adapters.driven.mongo_mapper import game_to_document, document_to_game

# Поля, які потрібні таблиці каталогу (великі тексти не читаємо)
LIST_PROJECTION = {"name": 1, "release_date": 1, "price": 1, "genres": 1, "developers": 1,
                   "platforms": 1, "positive": 1, "negative": 1}

SORTS = {
    "release_desc": [("release_date", DESCENDING), ("_id", ASCENDING)],
    "release_asc": [("release_date", ASCENDING), ("_id", ASCENDING)],
    "price_asc": [("price", ASCENDING), ("_id", ASCENDING)],
    "price_desc": [("price", DESCENDING), ("_id", ASCENDING)],
    "positive_desc": [("positive", DESCENDING), ("_id", ASCENDING)],
    "ccu_desc": [("peak_ccu", DESCENDING), ("_id", ASCENDING)],
    "name_asc": [("name", ASCENDING), ("_id", ASCENDING)],
}

# Вторинні індекси під фільтри та сортування каталогу.
# Хешований індекс {_id: "hashed"} створюється командою shardCollection (infra/mongo).
INDEXES = [
    ([("genres", ASCENDING)], "genres_1"),
    ([("platforms", ASCENDING)], "platforms_1"),
    ([("developers", ASCENDING)], "developers_1"),
    ([("release_date", DESCENDING)], "release_date_-1"),
    ([("price", ASCENDING)], "price_1"),
    ([("positive", DESCENDING)], "positive_-1"),
    ([("peak_ccu", DESCENDING)], "peak_ccu_-1"),
    ([("name", ASCENDING)], "name_1"),
]


class MongoAdapter(GameDocumentRepositoryPort):
    """MongoDB (через маршрутизатор mongos): основне сховище документа гри.

    Запис - з write concern majority (підтвердження більшістю реплік шарду, CP).
    Читання - з Secondary, якщо вони доступні (AP), крім читання для синхронізації.
    """

    def __init__(self, client, db_name: str = "steam", collection: str = "games"):
        self.db = client[db_name]
        base = self.db[collection]
        self.writes = base.with_options(write_concern=WriteConcern(w="majority", wtimeout=10000))
        self.reads = base.with_options(read_preference=ReadPreference.SECONDARY_PREFERRED)
        self.primary_reads = base.with_options(read_preference=ReadPreference.PRIMARY)

    def ensure_indexes(self) -> None:
        for keys, name in INDEXES:
            self.writes.create_index(keys, name=name)

    # ------------------------------------------------------------ Create
    def save(self, game: Game) -> Game:
        self.writes.insert_one(game_to_document(game))
        return game

    def save_many(self, games: List[Game]) -> int:
        """Пакетний upsert: повторне завантаження датасету не створює дублікатів."""
        if not games:
            return 0
        ops = [ReplaceOne({"_id": g.game_id}, game_to_document(g), upsert=True) for g in games]
        result = self.writes.bulk_write(ops, ordered=False)
        return result.upserted_count + result.matched_count

    def next_game_id(self) -> int:
        last = list(self.primary_reads.find({}, {"_id": 1}).sort("_id", DESCENDING).limit(1))
        return (last[0]["_id"] + 1) if last else 1

    # ------------------------------------------------------------ Read
    def find_by_id(self, game_id: int) -> Optional[Game]:
        doc = self.reads.find_one({"_id": int(game_id)})            # цільовий запит в один шард
        return document_to_game(doc) if doc else None

    def find_by_ids(self, game_ids: List[int], from_primary: bool = False) -> List[Game]:
        if not game_ids:
            return []
        coll = self.primary_reads if from_primary else self.reads
        return [document_to_game(d) for d in coll.find({"_id": {"$in": [int(i) for i in game_ids]}})]

    def find_all(self, limit: int = 50, offset: int = 0) -> List[Game]:
        cursor = self.reads.find({}, LIST_PROJECTION).sort("_id", ASCENDING).skip(offset).limit(limit)
        return [document_to_game(d) for d in cursor]

    @staticmethod
    def build_query(f: GameFilterDTO) -> dict:
        query = {}
        if f.genre:
            query["genres"] = f.genre                       # пошук елемента в масиві
        if f.platform:
            query["platforms"] = f.platform
        if f.year_from or f.year_to:
            date_range = {}
            if f.year_from:
                date_range["$gte"] = datetime(int(f.year_from), 1, 1)
            if f.year_to:
                date_range["$lt"] = datetime(int(f.year_to) + 1, 1, 1)
            query["release_date"] = date_range
        if f.max_price is not None:
            query["price"] = {"$lte": float(f.max_price)}
        if f.name_prefix:
            query["name"] = {"$regex": "^" + re.escape(f.name_prefix.strip()), "$options": "i"}
        return query

    def find_page(self, game_filter: GameFilterDTO) -> Tuple[List[Game], int]:
        query = self.build_query(game_filter)
        cursor = (self.reads.find(query, LIST_PROJECTION)
                  .sort(SORTS.get(game_filter.sort, SORTS["release_desc"]))
                  .skip(game_filter.offset)
                  .limit(game_filter.page_size))
        games = [document_to_game(d) for d in cursor]
        total = self.reads.count_documents(query)
        return games, total

    def distinct_values(self, field_name: str) -> List[str]:
        values = self.reads.distinct(field_name)
        return sorted(v for v in values if v)

    # ------------------------------------------------------------ Update
    def update(self, game: Game) -> Game:
        doc = game_to_document(game)
        doc.pop("_id")
        result = self.writes.update_one({"_id": game.game_id}, {"$set": doc})
        if result.matched_count == 0:
            raise KeyError(f"Гру {game.game_id} не знайдено")
        return game

    # ------------------------------------------------------------ Delete
    def delete_by_id(self, game_id: int) -> bool:
        return self.writes.delete_one({"_id": int(game_id)}).deleted_count == 1


__all__ = ["MongoAdapter", "DuplicateKeyError"]
