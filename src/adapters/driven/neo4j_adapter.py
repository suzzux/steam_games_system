from typing import List
from src.ports.outbound import GraphQueryPort

class Neo4jAdapter(GraphQueryPort):
    """Neo4j: графова БД для зв'язків між іграми, дизайнерами, платформами тощо"""

    # Cypher-запит: ігри, які зробив дизайнер X і які вийшли на платформі Y
    FIND_BY_PLATFORM_AND_DESIGNER = """
        MATCH (d:Designer {name: $designer})-[:DESIGNED]->(g:Game)-[:AVAILABLE_ON]->(p:Platform {name: $platform})
        RETURN g.game_id AS game_id
    """

    def __init__(self, driver=None):
        # driver = neo4j.GraphDatabase.driver(uri, auth=(user, password))
        self.driver = driver

    def find_games_by_platform_and_designer(self, platform: str, designer: str) -> List[int]: pass