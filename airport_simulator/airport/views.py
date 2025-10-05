from django.shortcuts import render
from .models import Airport
from django.forms.models import model_to_dict
from django.http import JsonResponse
from .models import Entity
from django.shortcuts import render
from airport.consumer import AirportConsumer
from django.views.decorators.csrf import csrf_exempt

# Create your views here.

def home(request):
    return render(request,'airport/home.html')

@csrf_exempt
def web_socket_notification_reciever(request):
    message = request.POST.get("message")
    AirportConsumer().push_notifications(message)
    return JsonResponse({})

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
    return JsonResponse(d)

