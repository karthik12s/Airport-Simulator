from django.shortcuts import render
from django.http import HttpResponse
from .models import Airport
from .schedulers.flight_scheduler import FlightSchedulerService
from .schedulers.gate_assigner import GateScheduleService
from .schedulers.baggage_assigner import BaggageScheduleService
from .schedulers.ATCService import ATCService
from .services import airport_service
from datetime import timezone
from django.core import serializers
from django.forms.models import model_to_dict
from django.http import JsonResponse
from .models import Entity
from django.shortcuts import render

# Create your views here.

def home(request):
    # t = Airport.objects.all()

    # d = {}
    # for i in t:
    #     d[i.code] = model_to_dict(i)
    #     terminal_dict = {}
    #     for terminal in i.terminals.all():
    #         gates = []
    #         baggages = []
    #         for entity in terminal.airport_entity.all():
    #             if entity.entity == Entity.BAGGAGE:
    #                 baggages.append(model_to_dict(entity))
    #             else:
    #                 gates.append(model_to_dict(entity))
    #         terminal = model_to_dict(terminal)
    #         terminal['gates'] = gates
    #         terminal['baggages'] = baggages
    #         terminal_dict[terminal['id']] = terminal
    #     d[i.code]['terminal'] = terminal_dict
    # print(d)
    # # print(t,t.terminals)
    # return JsonResponse(d)

    return render(request,'airport/home.html')


def airports(request):
    t = Airport.objects.all()

    d = {}
    for i in t:
        d[i.code] = model_to_dict(i)
        terminal_dict = {}
        for terminal in i.terminals.all():
            gates = []
            baggages = []
            for entity in terminal.airport_entity.all():
                if entity.entity == Entity.BAGGAGE:
                    baggages.append(model_to_dict(entity))
                else:
                    gates.append(model_to_dict(entity))
            terminal = model_to_dict(terminal)
            terminal['gates'] = gates
            terminal['baggages'] = baggages
            terminal_dict[terminal['id']] = terminal
        d[i.code]['terminal'] = terminal_dict
    print(d)
    # print(t,t.terminals)
    return JsonResponse(d)

