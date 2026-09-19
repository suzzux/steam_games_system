from src.ports.outbound import EventPublisherPort

class KafkaEventPublisherAdapter(EventPublisherPort):
    def publish_game_created_event(self, game_id: int) -> None: pass