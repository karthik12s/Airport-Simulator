import json
from django.forms.models import model_to_dict
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.db.models import Q
from django.utils import timezone

from .models import Airport, FlightInstance, AirportEntity, Entity,FlightState,Terminal
from airport.consumer import AirportConsumer

def serialize_airport_with_entities(airport):

    airport_data = model_to_dict(airport)
    terminal_dict = {}
    
    terminals = airport.terminals.prefetch_related('airport_entity').all()
    
    for terminal in terminals:
        terminal_data = model_to_dict(terminal)
        gates = []
        baggages = []
        
        for entity in terminal.airport_entity.all():
            entity_data = model_to_dict(entity)
            if entity.entity == Entity.GATE:
                gates.append(entity_data)
            else:
                baggages.append(entity_data)
        
        terminal_data['gates'] = gates
        terminal_data['baggages'] = baggages
        terminal_dict[str(terminal.id)] = terminal_data # Use str(id) for JSON keys
        
    airport_data['terminals'] = terminal_dict
    return airport_data

def home(request):
    return render(request, 'airport/home.html')

def get_flights(request):

    if request.method != 'GET':
        return JsonResponse({"message": "Only GET requests are valid."}, status=405)

    airport_code = request.GET.get('airport', '')
    count = int(request.GET.get('count', 15))

    queryset = FlightInstance.objects.all()

    if airport_code:
        queryset = queryset.filter(Q(source__code=airport_code) | Q(destination__code=airport_code))
        
    flights = queryset.exclude(state = FlightState.PENDING).order_by('-departure_time')[:count]

    if not flights.exists():
        return JsonResponse({"message": "No flights found."}, status=404)

    flights_list = [model_to_dict(flight) for flight in flights]
    
    return JsonResponse(flights_list, safe=False)

@csrf_exempt
def web_socket_notification_reciever(request):
    
    if request.method != 'POST':
        return JsonResponse({"message": "Only POST requests are valid."}, status=405)

    try:
        data = json.loads(request.body)
        message = data.get("message")
        if message:
            AirportConsumer().push_notifications(message)
            return JsonResponse({"message": "Notification received successfully."})
        else:
            return JsonResponse({"message": "Message field is missing."}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({"message": "Invalid JSON format."}, status=400)
    except Exception as e:
        return JsonResponse({"message": f"An error occurred: {str(e)}"}, status=500)


def all_airports(request):
    
    if request.method != 'GET':
        return JsonResponse({"message": "Only GET requests are valid."}, status=405)
    
    airports = Airport.objects.all()
    airport_data = []
    for  airport in airports:
        airport_data.append({
            'id':airport.code,
            'name':airport.name,
            'city':''
        })
    return JsonResponse(airport_data, safe=False)

def terminal_processor(entities):
    terminals = {}

    for i in entities:
        airport_code = i.terminal.airport.code
        terminal_id = i.terminal.id
        airport_entity = 'gates' if i.entity == Entity.GATE else 'baggages'
        if airport_code not in terminals:
            terminals[airport_code] = {}
        if terminal_id not in terminals[airport_code]:
            terminals[airport_code][terminal_id] = {"id":terminal_id,"name":i.terminal.code,'gates':[],'baggages':[]}
        entity_dict = model_to_dict(i)
        if entity_dict['free_at'] < timezone.now():
            entity_dict['status'] = 'Free'
        else:
            entity_dict['status'] = 'Occupied'
        terminals[airport_code][terminal_id][airport_entity].append(entity_dict)
    for i in terminals:
        d = terminals[i]
        l = []
        for j in d:
            l.append(d[j])
        terminals[i] = l
    return terminals

def all_terminals(request):

    if request.method != 'GET':
        return JsonResponse({"message": "Only GET requests are valid."}, status=405)
    
    entities = AirportEntity.objects.all()
    terminals = terminal_processor(entities)
    

    return JsonResponse(terminals,safe=False)
            

def get_terminals(request):

    if request.method != 'GET':
        return JsonResponse({"message": "Only GET requests are valid."}, status=405)
    
    airport_code = request.GET.get('airport', '')
    entities = AirportEntity.objects.filter(terminal__airport__code = airport_code)
    terminals = terminal_processor(entities)
    

    return JsonResponse(terminals,safe=False)


def airports_detailed(request):
    
    if request.method != 'GET':
        return JsonResponse({"message": "Only GET requests are valid."}, status=405)

    airports = Airport.objects.prefetch_related('terminals__airport_entity').all()[:2]
    
    if not airports.exists():
        return JsonResponse({"message": "No airports found."}, status=404)

    airport_dict = {
        airport.code: serialize_airport_with_entities(airport)
        for airport in airports
    }
    
    return JsonResponse(airport_dict, safe=False)