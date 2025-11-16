from django.urls import path
from . import views

urlpatterns = [
    path("",views.home,name="airport-home"),
    path("get_flights",views.get_flights),
    path("all_airports",views.all_airports),
    path("all_terminals",views.all_terminals),
    path("terminals",views.get_terminals),
    path("web_socket_notification_reciever",views.web_socket_notification_reciever,name = "websocket-recievers")
]
