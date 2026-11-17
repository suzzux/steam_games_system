import json
from datetime import datetime, timezone

from src.ports.outbound import EventPublisherPort

TOPIC = "game.events"
EVENT_UPSERTED = "game.upserted"
EVENT_DELETED = "game.deleted"


def make_event(event_type: str, game_id: int) -> dict:
    return {"type": event_type, "game_id": int(game_id),
            "occurred_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}


class KafkaEventPublisherAdapter(EventPublisherPort):
    """Публікація подій у топік game.events.

    Ключ повідомлення = game_id, тому всі події однієї гри потрапляють в одну
    партицію Kafka і обробляються sync-worker'ом по порядку.
    """

    def __init__(self, producer, topic: str = TOPIC):
        # producer = kafka.KafkaProducer(bootstrap_servers=..., acks="all", ...)
        self.producer = producer
        self.topic = topic

    @classmethod
    def create(cls, bootstrap_servers: str, topic: str = TOPIC):
        from kafka import KafkaProducer
        producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            acks="all",                       # подія вважається записаною, коли її підтвердили репліки
            linger_ms=20,                     # дрібні повідомлення збираються в пакети
            key_serializer=lambda k: str(k).encode(),
            value_serializer=lambda v: json.dumps(v).encode(),
        )
        return cls(producer, topic)

    def publish_game_created_event(self, game_id: int) -> None:
        self.producer.send(self.topic, key=game_id, value=make_event(EVENT_UPSERTED, game_id))

    def publish_game_deleted_event(self, game_id: int) -> None:
        self.producer.send(self.topic, key=game_id, value=make_event(EVENT_DELETED, game_id))

    def flush(self) -> None:
        self.producer.flush()
