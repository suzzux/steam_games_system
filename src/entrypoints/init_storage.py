"""Одноразова ініціалізація сховищ: індекси MongoDB, індекс Elasticsearch, обмеження Neo4j.

python -m src.entrypoints.init_storage
"""
import logging

from src.bootstrap import build_adapters, setup_logging
from src.config import Settings

log = logging.getLogger("steam_app")


def main():
    settings = Settings()
    setup_logging(settings)
    c = build_adapters(settings, with_publisher=False)
    c.repository.ensure_indexes()
    log.info("MongoDB: вторинні індекси створено")
    c.search.ensure_index()
    log.info("Elasticsearch: індекс games_search готовий")
    c.graph.ensure_constraints()
    log.info("Neo4j: унікальні обмеження створено")


if __name__ == "__main__":
    main()
