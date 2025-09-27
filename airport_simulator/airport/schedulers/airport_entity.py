from datetime import datetime, timezone, timedelta
from ..models import AirportEntity
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class EntityType(Enum):
    GATE = "GT"
    BAGGAGE = "BG"


class AirportEntityRepository:
    """Repository for fetching airport entities from DB."""

    @staticmethod
    def get_active_entities(entity_type: EntityType, airport_code: str, window_minutes: int = 120):
        current_time = datetime.now(timezone.utc)
        target_time = current_time + timedelta(minutes=window_minutes)

        entities = AirportEntity.objects.filter(
            free_at__lt=target_time,
            active=True,
            terminal__airport__code=airport_code,
            entity=entity_type.value
        ).order_by("free_at")

        logger.debug(f"Fetched {entities.count()} entities of type {entity_type} for airport {airport_code}")
        return entities


class AirportEntityHandler:
    """Singleton wrapper for airport entity queries."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AirportEntityHandler, cls).__new__(cls)
        return cls._instance

    def get_active_gates_for_airport(self, airport_code: str, window_minutes: int = 120):
        return AirportEntityRepository.get_active_entities(EntityType.GATE, airport_code, window_minutes)

    def get_active_baggages_for_airport(self, airport_code: str, window_minutes: int = 120):
        return AirportEntityRepository.get_active_entities(EntityType.BAGGAGE, airport_code, window_minutes)
