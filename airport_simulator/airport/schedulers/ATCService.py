from ..models import FlightInstance,Runway
from datetime import datetime,timezone,timedelta
from .flight_scheduler import FlightInstanceRepository
from .airport_entity import AirportEntityHandler
from collections import deque

a = AirportEntityHandler()

class RunwayRepository():

    @staticmethod
    def get_active_runways_for_airport(airport_code):
        return Runway.objects.filter(airport__code = airport_code,active = True)

class ATCService():

    def __init__(self,AirportEntityHandler=a,FlightInstanceRepository = FlightInstanceRepository,delay_time = 20):
        self.repo = AirportEntityHandler
        self.delay_time = delay_time
        self.flight_instance_repo = FlightInstanceRepository
    

    def add_take_off_flights_to_queue(self):
        upcoming_flights = FlightInstanceRepository.get_flights(state = 'PU')
        print(upcoming_flights,"upcoming_flights")
        airports_to_be_queried = {}
        for i in upcoming_flights:
            flights_ = airports_to_be_queried.get(i.code,[])
            flights_.append(i)
            airports_to_be_queried[i.source] = flights_
        print(airports_to_be_queried)
        for airport in airports_to_be_queried:
            runways = RunwayRepository.get_active_runways_for_airport(airport = airport.code)
            flights_ = airports_to_be_queried[airport]
            flight_state = 'PU'
            if len(list(runways))==0:
                flight_state = 'CA'
            for flight in flights_:
                flight.state = flight_state
                flight.save()
    
    def add_landing_flights_to_queue(self,window_minutes):
        current_time = datetime.now(timezone.utc)
        comparison_time = current_time + timedelta(minutes=window_minutes)
        upcoming_flights = FlightInstanceRepository.get_flights(arrival_time__lt = comparison_time)
        print(upcoming_flights,"upcoming_flights")
        airports_to_be_queried = {}
        for i in upcoming_flights:
            flights_ = airports_to_be_queried.get(i.code,[])
            flights_.append(i)
            airports_to_be_queried[i.source] = flights_
        print(airports_to_be_queried)
        for airport in airports_to_be_queried:
            runways = RunwayRepository.get_active_runways_for_airport(airport = airport.code)
            flights_ = airports_to_be_queried[airport]
            flight_state = 'AP'
            if len(list(runways))==0:
                flight_state = 'DIV'
            for flight in flights_:
                flight.state = flight_state
                flight.save()

    def merge_arrival_departure_flights(self,arrival_flights,departure_flights):
        ap = 0
        dp = 0
        return_list = []
        while ap<len(arrival_flights) and dp<len(departure_flights):
            if arrival_flights[ap].arrival_time < departure_flights[dp].departure_time+timedelta(minutes=10):
                return_list.append(arrival_flights[ap])
                ap+=1
            else:
                return_list.append(departure_flights[dp])
                dp+=1
        while ap<len(arrival_flights):
            return_list.append(arrival_flights[ap])
            ap+=1
        while dp<len(departure_flights):
            return_list.append(departure_flights[dp])
            dp+=1

        
    def assign_runways_for_airport(self,airport_code):
        arrival_flights_in_queue = self.flight_instance_repo.get_flights(state = "AP")
        arrival_flights_in_queue = list(sorted(arrival_flights_in_queue,key=lambda flight:flight.arrival_time))

        departure_flights_in_queue = self.flight_instance_repo.get_flights(state = "AP")
        departure_flights_in_queue = list(sorted(departure_flights_in_queue,key=lambda flight:flight.arrival_time))

        flight_list = self.merge_arrival_departure_flights(arrival_flights_in_queue,departure_flights_in_queue)

        runways = RunwayRepository.get_active_runways_for_airport(airport_code=airport_code)

        if len(runways)==0:
            for flight in flight_list:
                if flight.state == 'PU':
                    flight.state = 'CA'
                if flight.state == 'AP':
                    flight.state = 'DIV'
            self.flight_instance_repo.update_all(flight_list,attributes=['state'])
            return
        
        runways = list(sorted(runways,key=lambda x:x.free_at))
        flight_pointer = 0
        flights_to_be_updated = []
        for i in runways:
            if flight_pointer>=len(flight_list):
                break
            assigned = False
            while flight_pointer<len(flight_list) and not assigned:
                if flight_list[flight_pointer].state == 'AP':
                    if i.free_at> flight_list[flight_pointer].arrival_time + timedelta(minutes=30):
                        flight_list[flight_pointer].state = 'DIV'
                    else:
                        flight_list[flight_pointer].landing_runway = i
                        i.free_at = max(i.free_at+timedelta(minutes=5),flight_pointer[flight_pointer].arrival_time)
                        assigned  = True
                else:
                    flight_list[flight_pointer].landing_runway = i
                    i.free_at = max(i.free_at+timedelta(minutes=5),flight_pointer[flight_pointer].departure_time)
                flights_to_be_updated.append(flight_list[flight_pointer])
                flight_pointer+=1
                

            i.save()
            self.flight_instance_repo.update_all(flights_to_be_updated,attributes=['arrival_time','departure_time','state'])

                
        


from datetime import datetime, timezone, timedelta
from collections import deque
from ..models import Runway, FlightState


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
                else:
                    flight.landing_runway = runway
                    runway.free_at = max(runway.free_at + timedelta(minutes=5), flight.arrival_time)
                    flight.arrival_time = runway.free_at
            else:  # departure
                flight.take_off_runway = runway
                runway.free_at = max(runway.free_at , flight.departure_time)+ timedelta(minutes=5)
                flight.departure_time = runway.free_at - timedelta(minutes=5)

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

    def add_take_off_flights_to_queue(self):
        flights = self.flight_repo.get_flights(state=FlightState.PUSHBACK)
        self._update_queue(flights, FlightState.PUSHBACK, FlightState.CANCELLED)

    def add_landing_flights_to_queue(self, window_minutes=120):
        comparison_time = datetime.now(timezone.utc) + timedelta(minutes=window_minutes)
        flights = self.flight_repo.get_flights(arrival_time__lt=comparison_time)
        self._update_queue(flights, FlightState.INAPPROACH, FlightState.DIVERTED)

    def _update_queue(self, flights, ready_state, fail_state):
        grouped = self._group_by_airport(flights)
        for airport, flights in grouped.items():
            runways = self.runway_repo.get_active_runways_for_airport(airport)
            new_state = ready_state if runways else fail_state
            for flight in flights:
                flight.state = new_state
            self.flight_repo.update_all(flights, attributes=['state'])

    def assign_runways_for_airport(self, airport_code):
        arrivals = self.flight_repo.get_flights(state=FlightState.INAPPROACH)
        departures = self.flight_repo.get_flights(state=FlightState.PUSHBACK)
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
