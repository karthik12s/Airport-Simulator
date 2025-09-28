from django.apps import AppConfig
from .schedulers.main_scheduler import start


class AirportConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'airport'
    def ready(self):
        start()
