"""Налаштування з змінних оточення (значення за замовчуванням - для запуску поза Docker)."""
import os
from dataclasses import dataclass, field


def _env(name: str, default: str) -> str:
    return os.getenv(name, default)


@dataclass(frozen=True)
class Settings:
    mongo_uri: str = field(default_factory=lambda: _env("MONGO_URI", "mongodb://localhost:27017"))
    mongo_db: str = field(default_factory=lambda: _env("MONGO_DB", "steam"))
    elastic_url: str = field(default_factory=lambda: _env("ELASTIC_URL", "http://localhost:9200"))
    elastic_replicas: int = field(default_factory=lambda: int(_env("ELASTIC_REPLICAS", "0")))
    neo4j_uri: str = field(default_factory=lambda: _env("NEO4J_URI", "bolt://localhost:7687"))
    neo4j_user: str = field(default_factory=lambda: _env("NEO4J_USER", "neo4j"))
    neo4j_password: str = field(default_factory=lambda: _env("NEO4J_PASSWORD", "password123"))
    redis_url: str = field(default_factory=lambda: _env("REDIS_URL", "redis://localhost:6379/0"))
    kafka_servers: str = field(default_factory=lambda: _env("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"))
    log_file: str = field(default_factory=lambda: _env("LOG_FILE", "logs/app.log"))
