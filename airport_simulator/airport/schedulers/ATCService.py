from ..models import Runway, FlightState
from datetime import timedelta
from .flight_scheduler import FlightInstanceRepository
from .airport_entity import AirportEntityHandler
from collections import deque
from airport.schedulers.flight_background_scheduler import FlightScheduleJob
from airport.services.kafka_service import KafkaService
a = AirportEntityHandler()
kafka_service = KafkaService()

class RunwayRepository():

    @staticmethod
    def get_active_runways_for_airport(airport_code):
        return Runway.objects.filter(airport__code = airport_code,active = True)


class RunwayAllocator:

    def assign(self, flights, runways):
        runways = sorted(runways, key=lambda r: r.free_at)
        flights = deque(flights)
        updated_flights = []

        for runway in runways:
            if not flights:
                break
            flight = flights.popleft()

            if flight.state == FlightState.INAPPROACH:
                if runway.free_at > flight.arrival_time + timedelta(minutes=30):
                    flight.state = FlightState.DIVERTED
                    kafka_service.produce(message = f"Flight {flight.code} diverted from Airport {flight.destination.code}  due to Runway constraints")
                else:
                    flight.landing_runway = runway
                    runway.free_at = max(runway.free_at + timedelta(minutes=5), flight.arrival_time)
                    flight.arrival_time = runway.free_at
                    FlightScheduleJob.schedule_landing(flight=flight)
                    kafka_service.produce(message = f"Flight {flight.code} allotted with Runway {flight.landing_runway.number_1} Airport {flight.destination.code}  ")

            else:  # departure
                flight.take_off_runway = runway
                runway.free_at = max(runway.free_at , flight.departure_time)+ timedelta(minutes=5)
                flight.departure_time = runway.free_at
                flight.state = FlightState.TAXIOUT
                FlightScheduleJob.schedule_takeoff(flight=flight)
                kafka_service.produce(message = f"Flight {flight.code} allotted with Runway {flight.take_off_runway.number_1} Airport {flight.source.code}  ")


            updated_flights.append(flight)
            runway.save()

        return updated_flights


class ATCService:
    """ATC orchestrates scheduling of flights on runways."""

    def __init__(self, flight_repo=FlightInstanceRepository, runway_repo=RunwayRepository, delay_time=20):
        self.flight_repo = flight_repo
        self.runway_repo = runway_repo
        self.delay_time = delay_time
        self.allocator = RunwayAllocator()
    
    def start_ATC_scheduler(self):
        arrivals = self.flight_repo.get_flights(state=FlightState.INAPPROACH,landing_runway = None)
        departures = self.flight_repo.get_flights(state=FlightState.PUSHBACK,take_off_runway=None)
        unique_airports = set()
        for i in arrivals:
            unique_airports.add(i.destination.code)
        for i in departures:
            unique_airports.add(i.source.code)
        
        for i in unique_airports:
            self.assign_runways_for_airport(i)


    def assign_runways_for_airport(self, airport_code):
        arrivals = self.flight_repo.get_flights(destination__code = airport_code,state=FlightState.INAPPROACH,landing_runway = None)
        departures = self.flight_repo.get_flights(source__code = airport_code,state=FlightState.PUSHBACK,take_off_runway=None)
        flights = self._merge_flights(arrivals, departures)
        print(flights)

        runways = self.runway_repo.get_active_runways_for_airport(airport_code)
        print(runways)
        if not runways:
            for flight in flights:
                if flight.state == FlightState.PUSHBACK:
                    flight.state = FlightState.CANCELLED
                elif flight.state == FlightState.INAPPROACH:
                    flight.state = FlightState.DIVERTED
            self.flight_repo.update_all(flights, attributes=['state'])
            return

        updated = self.allocator.assign(flights, runways)
        self.flight_repo.update_all(updated, attributes=['arrival_time','departure_time','state','take_off_runway','landing_runway'])

    def _group_by_airport(self, flights):
        grouped = {}
        for f in flights:
            grouped.setdefault(f.source, []).append(f)
        return grouped

    def _merge_flights(self, arrivals, departures):
        """Merge arrivals and departures by time for scheduling fairness."""
        arrivals, departures = list(arrivals), list(departures)
        i, j = 0, 0
        merged = []
        while i < len(arrivals) and j < len(departures):
            if arrivals[i].arrival_time < departures[j].departure_time + timedelta(minutes=10):
                merged.append(arrivals[i]); i += 1
            else:
                merged.append(departures[j]); j += 1
        merged.extend(arrivals[i:])
        merged.extend(departures[j:])
        return merged
