"""sync-worker: python -m src.entrypoints.sync_worker"""
from src.bootstrap import build_adapters, setup_logging, retry
from src.config import Settings
from src.services.sync_service import GameSyncService
from src.adapters.driving.kafka_consumer import KafkaSyncConsumer


def main():
    settings = Settings()
    setup_logging(settings)
    c = build_adapters(settings, with_publisher=False)
    sync = GameSyncService(c.repository, c.search, c.graph, c.cache)
    consumer = retry("Kafka", lambda: KafkaSyncConsumer(sync, settings.kafka_servers))
    consumer.run_forever()


if __name__ == "__main__":
    main()
