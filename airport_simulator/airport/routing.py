from django.urls import path
from .consumer import *

websocket_urlpatterns = [
    path("airport/socket",AirportConsumer.as_asgi())
]