from typing import List
from src.ports.outbound import RelationalQueryPort

class PostgresAdapter(RelationalQueryPort):
    def find_games_by_platform_and_designer(self, platform: str, designer: str) -> List[int]: pass