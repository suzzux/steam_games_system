from typing import List

from src.ports.outbound import GraphQueryPort
from src.domain.entities import Game

CONSTRAINTS = [
    "CREATE CONSTRAINT game_id IF NOT EXISTS FOR (g:Game) REQUIRE g.game_id IS UNIQUE",
    "CREATE CONSTRAINT studio_name IF NOT EXISTS FOR (n:Studio) REQUIRE n.name IS UNIQUE",
    "CREATE CONSTRAINT designer_name IF NOT EXISTS FOR (n:Designer) REQUIRE n.name IS UNIQUE",
    "CREATE CONSTRAINT genre_name IF NOT EXISTS FOR (n:Genre) REQUIRE n.name IS UNIQUE",
    "CREATE CONSTRAINT platform_name IF NOT EXISTS FOR (n:Platform) REQUIRE n.name IS UNIQUE",
    "CREATE CONSTRAINT engine_name IF NOT EXISTS FOR (n:Engine) REQUIRE n.name IS UNIQUE",
]

# Пакетний upsert. FOREACH замість UNWIND, бо порожній список у UNWIND обриває решту запиту (див. розділ 3.2).
# Старі вихідні зв'язки гри видаляються, щоб після оновлення не лишалось зайвих ребер.
UPSERT_GAMES = """
UNWIND $rows AS row
MERGE (g:Game {game_id: row.game_id})
SET g.name = row.name
WITH g, row
OPTIONAL MATCH (g)-[old]->()
DELETE old
WITH DISTINCT g, row
FOREACH (x IN row.genres     | MERGE (n:Genre {name: x})    MERGE (g)-[:HAS_GENRE]->(n))
FOREACH (x IN row.developers | MERGE (n:Studio {name: x})   MERGE (g)-[:DEVELOPED_BY]->(n))
FOREACH (x IN row.publishers | MERGE (n:Studio {name: x})   MERGE (g)-[:PUBLISHED_BY]->(n))
FOREACH (x IN row.designers  | MERGE (n:Designer {name: x}) MERGE (g)-[:DESIGNED_BY]->(n))
FOREACH (x IN row.platforms  | MERGE (n:Platform {name: x}) MERGE (g)-[:ON_PLATFORM]->(n))
FOREACH (x IN row.engines    | MERGE (n:Engine {name: x})   MERGE (g)-[:USES_ENGINE]->(n))
"""

DELETE_GAMES = "UNWIND $ids AS id MATCH (g:Game {game_id: id}) DETACH DELETE g"

# Ігри, які зробив дизайнер X і які вийшли на платформі Y (напрямки зв'язків як у розділі 1.4.3)
FIND_BY_PLATFORM_AND_DESIGNER = """
MATCH (d:Designer {name: $designer})<-[:DESIGNED_BY]-(g:Game)-[:ON_PLATFORM]->(p:Platform {name: $platform})
RETURN g.game_id AS game_id
ORDER BY g.name
LIMIT $limit
"""


def game_to_row(game: Game) -> dict:
    return {
        "game_id": game.game_id,
        "name": game.name,
        "genres": [g.name for g in game.genres],
        "developers": [s.name for s in game.developers],
        "publishers": [s.name for s in game.publishers],
        "designers": [d.name for d in game.designers],
        "platforms": [p.name for p in game.platforms],
        "engines": [game.engine.name] if game.engine.name else [],
    }


class Neo4jAdapter(GraphQueryPort):
    """Neo4j: графова БД для зв'язків між іграми, дизайнерами, платформами тощо"""

    def __init__(self, driver, database: str = "neo4j"):
        # driver = neo4j.GraphDatabase.driver(uri, auth=(user, password))
        self.driver = driver
        self.database = database

    def ensure_constraints(self) -> None:
        with self.driver.session(database=self.database) as session:
            for statement in CONSTRAINTS:
                session.run(statement).consume()

    def upsert_games(self, games: List[Game]) -> int:
        rows = [game_to_row(g) for g in games]
        with self.driver.session(database=self.database) as session:
            session.execute_write(lambda tx: tx.run(UPSERT_GAMES, rows=rows).consume())
        return len(rows)

    def delete_games(self, game_ids: List[int]) -> None:
        with self.driver.session(database=self.database) as session:
            session.execute_write(lambda tx: tx.run(DELETE_GAMES, ids=list(game_ids)).consume())

    def find_games_by_platform_and_designer(self, platform: str, designer: str, limit: int = 100) -> List[int]:
        with self.driver.session(database=self.database) as session:
            records = session.execute_read(
                lambda tx: list(tx.run(FIND_BY_PLATFORM_AND_DESIGNER, platform=platform,
                                       designer=designer, limit=limit)))
        return [r["game_id"] for r in records]
