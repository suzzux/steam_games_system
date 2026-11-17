"""Composition root: тут створюються підключення, адаптери і сервіси.

Тільки цей модуль знає про конкретні бібліотеки (pymongo, elasticsearch, neo4j, redis, kafka);
решта коду працює з портами.
"""
import logging
import os
import sys
import time
from dataclasses import dataclass

from src.config import Settings

log = logging.getLogger("steam_app")


def setup_logging(settings: Settings) -> None:
    os.makedirs(os.path.dirname(settings.log_file) or ".", exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler(settings.log_file, encoding="utf-8")],
    )


def retry(what: str, func, attempts: int = 40, delay: float = 3.0):
    """Сервіси в контейнерах стартують не одночасно, тому підключення повторюється (як у розділі 3.2)."""
    for attempt in range(1, attempts + 1):
        try:
            return func()
        except Exception as error:  # noqa: BLE001 - нам важливий будь-який збій підключення
            log.warning("%s ще не готовий (%d/%d): %s", what, attempt, attempts, type(error).__name__)
            time.sleep(delay)
    raise RuntimeError(f"Не вдалося підключитися: {what}")


@dataclass
class Container:
    settings: Settings
    mongo_client: object
    repository: object
    analytics_adapter: object
    search: object
    graph: object
    cache: object
    publisher: object


def build_adapters(settings: Settings, with_publisher: bool = True) -> Container:
    from pymongo import MongoClient
    from elasticsearch import Elasticsearch
    from neo4j import GraphDatabase
    import redis

    from src.adapters.driven.mongo_adapter import MongoAdapter
    from src.adapters.driven.mongo_shard_adapter import MongoShardAnalyticsAdapter
    from src.adapters.driven.elastic_adapter import ElasticAdapter
    from src.adapters.driven.neo4j_adapter import Neo4jAdapter
    from src.adapters.driven.redis_adapter import RedisAdapter
    from src.adapters.driven.kafka_adapter import KafkaEventPublisherAdapter

    mongo_client = MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=5000)
    retry("MongoDB (mongos)", lambda: mongo_client.admin.command("ping"))

    es = Elasticsearch(settings.elastic_url, request_timeout=30)
    retry("Elasticsearch", lambda: es.info())

    driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
    retry("Neo4j", driver.verify_connectivity)

    redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    retry("Redis", redis_client.ping)

    publisher = None
    if with_publisher:
        publisher = retry("Kafka", lambda: KafkaEventPublisherAdapter.create(settings.kafka_servers))

    return Container(
        settings=settings,
        mongo_client=mongo_client,
        repository=MongoAdapter(mongo_client, settings.mongo_db),
        analytics_adapter=MongoShardAnalyticsAdapter(mongo_client, settings.mongo_db),
        search=ElasticAdapter(es, replicas=settings.elastic_replicas),
        graph=Neo4jAdapter(driver),
        cache=RedisAdapter(redis_client),
        publisher=publisher,
    )


def build_controller(c: Container):
    from src.services.command_service import GameCommandService
    from src.services.query_service import GameQueryService
    from src.services.analytics_service import ShardAnalyticsService, MonitoringService
    from src.adapters.driving.api_controller import GameAPIController

    commands = GameCommandService(c.repository, c.publisher, c.cache)
    queries = GameQueryService(c.cache, c.search, c.graph, c.repository, shard_info=c.analytics_adapter)
    return GameAPIController(
        command_port=commands, update_port=commands, delete_port=commands,
        list_port=queries, details_port=queries, search_port=queries, filter_port=queries,
        analytics_port=ShardAnalyticsService(c.analytics_adapter),
        monitoring_port=MonitoringService(c.cache),
    )
