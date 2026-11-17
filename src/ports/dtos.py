from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ---------------------------------------------------------------- команди (запис)
@dataclass
class GameCreateCommandDTO:
    name: str
    price: float
    min_age: int
    release_date: str
    short_description: str
    detailed_description: str
    engine: str
    genres: List[str] = field(default_factory=list)
    developers: List[str] = field(default_factory=list)
    publishers: List[str] = field(default_factory=list)
    designers: List[str] = field(default_factory=list)
    platforms: List[str] = field(default_factory=list)
    game_id: Optional[int] = None
    game_trailer: str = ""
    reviews: str = ""
    dlc_count: int = 0
    achievements: int = 0
    estimated_owners: str = "0 - 20000"
    peak_ccu: int = 0
    positive: int = 0
    negative: int = 0
    recommendations: int = 0
    average_playtime_forever: int = 0
    median_playtime_2weeks: int = 0
    categories: List[str] = field(default_factory=list)
    supported_languages: List[str] = field(default_factory=list)
    full_audio_languages: List[str] = field(default_factory=list)


@dataclass
class IngestReportDTO:
    """Результат пакетного завантаження (генератор / завантажувач датасету)."""
    processed: int = 0
    saved: int = 0
    failed: int = 0
    errors: List[str] = field(default_factory=list)


# ---------------------------------------------------------------- запити (читання)
@dataclass
class GameResponseDTO:
    """Повна картка гри, яку отримує клієнт (UI або API)."""
    game_id: int
    name: str
    price: float
    name_with_price: Optional[str] = None
    release_date: str = ""
    required_age: int = 0
    short_description: str = ""
    detailed_description: str = ""
    reviews: str = ""
    genres: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    developers: List[str] = field(default_factory=list)
    publishers: List[str] = field(default_factory=list)
    designers: List[str] = field(default_factory=list)
    platforms: List[str] = field(default_factory=list)
    engine: str = ""
    game_trailer: str = ""
    supported_languages: List[str] = field(default_factory=list)
    full_audio_languages: List[str] = field(default_factory=list)
    dlc_count: int = 0
    achievements: int = 0
    estimated_owners: str = ""
    peak_ccu: int = 0
    positive: int = 0
    negative: int = 0
    recommendations: int = 0
    average_playtime_forever: int = 0
    median_playtime_2weeks: int = 0
    positive_ratio: float = 0.0
    engagement_score: float = 0.0
    shard: Optional[str] = None  # у якому шарді MongoDB лежить документ


@dataclass
class GameListItemDTO:
    """Короткий запис для таблиці каталогу."""
    game_id: int
    name: str
    release_date: str
    price: float
    genres: List[str]
    developers: List[str]
    platforms: List[str]
    positive_ratio: float


@dataclass
class GameFilterDTO:
    """Параметри сторінки каталогу (фільтри, сортування, пагінація)."""
    genre: Optional[str] = None
    platform: Optional[str] = None
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    max_price: Optional[float] = None
    name_prefix: Optional[str] = None
    sort: str = "release_desc"  # release_desc | release_asc | price_asc | price_desc | positive_desc | ccu_desc | name_asc
    page: int = 1
    page_size: int = 25

    def __post_init__(self):
        self.page = max(1, int(self.page or 1))
        self.page_size = min(100, max(1, int(self.page_size or 25)))

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


@dataclass
class PageDTO:
    items: List[GameListItemDTO]
    total: int
    page: int
    page_size: int

    @property
    def pages(self) -> int:
        return max(1, -(-self.total // self.page_size))


@dataclass
class FacetsDTO:
    """Значення для випадних списків фільтрів."""
    genres: List[str] = field(default_factory=list)
    platforms: List[str] = field(default_factory=list)


@dataclass
class SearchResultDTO:
    query: str
    items: List[GameListItemDTO]
    source: str          # "redis" (кеш) | "elasticsearch" | "neo4j"
    elapsed_ms: float


# ---------------------------------------------------------------- шардинг і map-reduce
@dataclass
class MapReduceQueryDTO:
    group_by: str = "genres"   # genres | platforms | engine | developers | publishers | game_designers
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    platform: Optional[str] = None
    top_n: int = 20
    verify: bool = True        # порівняти результат з агрегацією через mongos


@dataclass
class GroupStatDTO:
    key: str
    games: int
    avg_price: float
    positive_ratio: float
    max_peak_ccu: int
    free_share: float


@dataclass
class ShardPartialDTO:
    """Проміжний (map) результат одного шарду."""
    shard: str
    matched_docs: int
    groups: int
    elapsed_ms: float


@dataclass
class MapReduceResultDTO:
    query: MapReduceQueryDTO
    rows: List[GroupStatDTO]
    shards: List[ShardPartialDTO]
    total_groups: int
    elapsed_ms: float
    verified: Optional[bool] = None


@dataclass
class ShardDistributionDTO:
    shard: str
    documents: int
    size_mb: float
    chunks: int
    share: float = 0.0


@dataclass
class MonitoringDTO:
    counters: Dict[str, int] = field(default_factory=dict)
