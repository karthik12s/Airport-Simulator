from ..models import FlightInstance
from datetime import datetime,timezone,timedelta
from .airport_entity import AirportEntityHandler
from .flight_scheduler import FlightInstanceRepository
from collections import deque
import logging
from .flight_background_scheduler import FlightScheduleJob
from airport.services.kafka_service import KafkaService

flight_job_scheduler = FlightScheduleJob()

gate_repository = AirportEntityHandler()

logger = logging.getLogger(__name__)
logger.setLevel = logging.INFO

# ---------- Time Calculator ----------
class GateTimeCalculator:
    DEFAULT_OCCUPANCY = 60  # minutes

    @staticmethod
    def assign_gate_time(gate, flight, delay=20):
        """
        Updates gate and flight timings when assigned.
        """
        gate.free_at = max(gate.free_at+timedelta(minutes=GateTimeCalculator.DEFAULT_OCCUPANCY),flight.departure_time) 
        flight.gate = gate
        flight.departure_time = gate.free_at
        flight.state = "G"
        return gate, flight

    @staticmethod
    def delay_flight(flight, delay=20):
        flight.departure_time += timedelta(minutes=delay)
        return flight



class GateRepository:
    def __init__(self, airport_entity_handler):
        self.handler = airport_entity_handler

    def get_gates_for_airport(self, airport_code):
        return self.handler.get_active_gates_for_airport(airport=airport_code)


class FlightQueueFactory:
    @staticmethod
    def build_flight_queue(flights):
        return deque(sorted(flights, key=lambda f: f.departure_time))


class GateScheduleService:
    def __init__(self, flight_repo = FlightInstanceRepository, gate_repo = gate_repository, calculator=GateTimeCalculator, delay_time=20):
        self.flight_repo = flight_repo
        self.gate_repo = gate_repo
        self.calculator = calculator
        self.delay_time = delay_time

    def assign_gates(self, window_minutes=120):
        current_time = datetime.now(timezone.utc)
        comparison_time = current_time + timedelta(minutes=window_minutes)
        print(comparison_time,current_time,datetime.now(timezone.utc))
        # fetch flights
        upcoming_flights = self.flight_repo.get_upcoming_flights(comparison_time)
        print(upcoming_flights)
        logger.info("Upcoming flights: %d", len(upcoming_flights))

        # group by airport source
        airport_to_flights = {}
        for flight in upcoming_flights:
            airport_to_flights.setdefault(flight.source.code, []).append(flight)

        updated_flights = []

        # iterate airport-wise
        for airport_code, flights in airport_to_flights.items():
            gates = self.gate_repo.get_active_gates_for_airport(airport_code)
            flight_queue = FlightQueueFactory.build_flight_queue(flights)

            for gate in gates:
                if not flight_queue:
                    break
                current_flight = flight_queue.popleft()
                gate, updated_flight = self.calculator.assign_gate_time(gate, current_flight)
                gate.save()
                updated_flights.append(updated_flight)
                KafkaService.produce(message = f"Flight {flight.code} assigned to Gate {flight.gate.code} Airport {flight.source.code} ")


            # delay remaining flights
            while flight_queue:
                current_flight = flight_queue.popleft()
                updated_flights.append(self.calculator.delay_flight(current_flight, self.delay_time))

        flight_job_scheduler.schedule_push_back(updated_flights)
        self.flight_repo.update_all(updated_flights,["departure_time", "state","gate"])
        logger.info("Assigned/Delayed %d flights", len(updated_flights))
        return updated_flights
    
        
        