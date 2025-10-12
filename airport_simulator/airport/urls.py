from django.urls import path
from . import views

urlpatterns = [
    path("",views.home,name="airport-home"),
    path("get_flights",views.get_flights),
    path("airports",views.airports),
    path("all_airports",views.all_airports),
    path("web_socket_notification_reciever",views.web_socket_notification_reciever,name = "websocket-recievers")
]
