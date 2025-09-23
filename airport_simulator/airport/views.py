from django.shortcuts import render
from django.http import HttpResponse
from .models import Airport
from .schedulers.flight_scheduler import FlightSchedulerService
from datetime import timezone

# Create your views here.

def home(request):
    print(Airport.objects.all())
    fs = FlightSchedulerService()
    t = fs.schedule(window_minutes=360)
    print(t)
    return HttpResponse("abc")