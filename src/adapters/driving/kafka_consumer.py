"""Driving-адаптер sync-worker: читає події з Kafka і викликає SyncGameProjectionPort."""
import json
import logging
from typing import Iterable, List, Tuple

from src.ports.inbound import SyncGameProjectionPort
from src.adapters.driven.kafka_adapter import TOPIC, EVENT_DELETED

log = logging.getLogger(__name__)


def split_events(events: Iterable[dict]) -> Tuple[List[int], List[int]]:
    """Для кожної гри важлива лише ОСТАННЯ подія в пакеті (upsert або delete)."""
    last = {}
    for event in events:
        last[int(event["game_id"])] = event["type"]
    upserts = [gid for gid, t in last.items() if t != EVENT_DELETED]
    deletes = [gid for gid, t in last.items() if t == EVENT_DELETED]
    return upserts, deletes


class KafkaSyncConsumer:

    def __init__(self, sync_port: SyncGameProjectionPort, bootstrap_servers: str,
                 topic: str = TOPIC, group_id: str = "sync-worker", batch_size: int = 500):
        from kafka import KafkaConsumer
        self.sync_port = sync_port
        self.consumer = KafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            enable_auto_commit=False,          # offset фіксуємо тільки після успішної обробки
            auto_offset_reset="earliest",
            value_deserializer=lambda b: json.loads(b.decode()),
            max_poll_records=batch_size,
        )

    def run_forever(self) -> None:
        log.info("sync-worker слухає топік %s", TOPIC)
        while True:
            polled = self.consumer.poll(timeout_ms=1000)
            events = [msg.value for messages in polled.values() for msg in messages]
            if not events:
                continue
            upserts, deletes = split_events(events)
            synced = self.sync_port.sync_games(upserts)
            removed = self.sync_port.remove_games(deletes)
            self.consumer.commit()             # at-least-once: при збої подія обробиться ще раз (запис ідемпотентний)
            log.info("Оброблено подій: %d (оновлено %d, видалено %d)", len(events), synced, removed)
