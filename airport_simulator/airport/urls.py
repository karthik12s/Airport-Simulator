from django.urls import path
from . import views

urlpatterns = [
    path("",views.home,name="airport-home"),
    path("airports",views.airports)
]
