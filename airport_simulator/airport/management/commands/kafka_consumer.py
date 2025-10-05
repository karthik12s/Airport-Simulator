from django.core.management.base import BaseCommand
from airport.services.kafka_service import KafkaService

class Command(BaseCommand):
    help = 'Starts the Kafka consumer to listen for messages.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting Kafka consumer..."))
        try:
            KafkaService().consume()
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\nKafka consumer stopped."))

