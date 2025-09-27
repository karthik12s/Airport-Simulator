from django.shortcuts import render
from django.http import HttpResponse
from .models import Airport
from .schedulers.flight_scheduler import FlightSchedulerService
from .schedulers.gate_assigner import GateScheduleService
from .schedulers.baggage_assigner import BaggageScheduleService

from .schedulers.ATCService import ATCService
from datetime import timezone

# Create your views here.

def home(request):
    print(Airport.objects.all())
    fs = FlightSchedulerService()
    t = fs.schedule(window_minutes=360)
    gs = GateScheduleService()

    print(t)
    g = gs.assign_gates()

    bs = BaggageScheduleService()
    b = bs.assign_baggage()
    print(b)
    print(g)
    a = ATCService()
    ab = a.assign_runways_for_airport('HYD')
    print(ab)

    return HttpResponse("abc")