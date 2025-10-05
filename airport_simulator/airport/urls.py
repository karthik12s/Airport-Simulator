from django.urls import path
from . import views

urlpatterns = [
    path("",views.home,name="airport-home"),
    path("airports",views.airports),
    path("web_socket_notification_reciever",views.web_socket_notification_reciever,name = "websocket-recievers")
]
