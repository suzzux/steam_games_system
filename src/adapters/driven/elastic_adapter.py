from typing import List
from src.ports.outbound import FullTextSearchPort

class ElasticAdapter(FullTextSearchPort):
    def search_by_text(self, text_query: str) -> List[int]: pass