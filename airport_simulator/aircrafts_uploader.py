import json
import django
import os
import random
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'airport_simulator.settings')
django.setup()

from airport.models import Aircraft, Airline, Airport, Terminal, AirportEntity, Entity, Runway, Flight

def load_data_from_json(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
        return []

def create_aircrafts():
    aircrafts_data = load_data_from_json('aircrafts.json')
    if not aircrafts_data: return
    
    print("Creating Aircrafts...")
    for i in aircrafts_data:
        Aircraft.objects.create(
            name=i['name'],
            manufacturer=i['manufacturer'],
            takeoff_req=i['takeoff_distance_metres'],
            landing_req=i['landing_distance_metres'],
            capacity=i['capacity']
        )
    print("Aircraft creation completed.")

def create_airlines():
    airlines_data = load_data_from_json('airlines.json')
    if not airlines_data: return

    for i in airlines_data:
        Airline.objects.create(
            name=i['name'],
            code=i['code'],
            active=True
        )
    print("Airline creation completed.")

def create_airports():
    airports_data = load_data_from_json('airports.json')
    if not airports_data: return

    print("Creating Airports...")
    for i in airports_data:
        Airport.objects.create(
            name=i['name'],
            code=i['code'],
            latitude=i['latitude'],
            longitude=i['longitude'],
            active=True,
            domestic=False
        )
    print("Airport creation completed.")

def create_terminals():
    print("Creating Terminals...")
    for airport in Airport.objects.all()[2:]:
        for j in range(random.randint(1, 3)):
            Terminal.objects.create(
                airport=airport,
                code=f"T{j}",
                capacity=200,
                domestic=False
            )
    print("Terminal creation completed.")

def create_airport_entities():
    print("Creating Airport Entities...")
    for terminal in Terminal.objects.all()[2:]:
        for entity_type in [Entity.BAGGAGE, Entity.GATE]:
            for j in range(random.randint(1, 3)):
                code = f"G{j}" if entity_type == Entity.GATE else f"B{j}"
                try:
                    AirportEntity.objects.create(
                        code=code,
                        capacity=random.randint(250, 350),
                        terminal=terminal,
                        entity=entity_type
                    )
                except django.db.utils.IntegrityError:
                    # Handle cases where the same entity is attempted to be created
                    pass
    print("Airport entity creation completed.")

def create_runways():
    runway_materials = ["Asphalt", "Concrete", "Asphalt_Concrete"]

    def other_end_number(num1):
        return (num1 + 18) % 36

    print("Creating Runways...")
    for airport in Airport.objects.all()[2:]:
        for j in range(random.randint(1, 3)):
            num1 = random.randint(0, 35)
            try:
                Runway.objects.create(
                    airport=airport,
                    length=random.randint(2000, 3500),
                    material=random.choice(runway_materials),
                    number_1=num1,
                    number_2=other_end_number(num1)
                )
            except django.db.utils.IntegrityError:
                # Handle cases where a unique constraint is violated
                break

def create_flights():
    flights_data = load_data_from_json('flights.json')
    if not flights_data: return
    

    aircraft_map = {a.name: a for a in Aircraft.objects.all()}
    airline_map = {a.name: a for a in Airline.objects.all()}
    airport_map = {a.code: a for a in Airport.objects.all()}

    for i in flights_data:
        try:
            source_airport = airport_map.get(i['source'])
            destination_airport = airport_map.get(i['destination'])
            aircraft = aircraft_map.get(i['Aircraft'])
            airline = airline_map.get(i['airline'])

            if not all([source_airport, destination_airport, aircraft, airline]):
                print(f"Skipping flight {i['code']} due to missing data.")
                continue

            Flight.objects.create(
                code=i['code'],
                source=source_airport,
                destination=destination_airport,
                arrival_time=datetime.strptime(i['arrival_time'], "%H:%M").time(),
                departure_time=datetime.strptime(i['departure_time'], "%H:%M").time(),
                airline=airline,
                Aircraft=aircraft,
                domestic=False
            )
        except Exception as e:
            print(f"Error creating flight {i.get('code', 'N/A')}: {e}")
            
    print("Flight creation completed.")

if __name__ == "__main__":
    create_aircrafts()
    create_airlines()
    create_airports()
    create_terminals()
    create_airport_entities()
    create_runways()
    create_flights()
    print("\nAll data loading processes finished.")