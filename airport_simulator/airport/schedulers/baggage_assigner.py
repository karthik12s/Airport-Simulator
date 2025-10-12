from datetime import timedelta
from .flight_scheduler import FlightInstanceRepository
from .airport_entity import AirportEntityHandler
from collections import deque
import logging
from airport.models import FlightState
from airport.services.kafka_service import KafkaService
from airport.schedulers.flight_background_scheduler import FlightScheduleJob

baggage_repository = AirportEntityHandler()               


logger = logging.getLogger(__name__)

class BaggageTimeCalculator:
    DEFAULT_HANDLING_TIME = 30  # minutes

    @staticmethod
    def assign_baggage_time(baggage, flight, delay=20):
        baggage.free_at = flight.arrival_time + timedelta(minutes=BaggageTimeCalculator.DEFAULT_HANDLING_TIME)
        flight.baggage = baggage
        flight.arrival_time = baggage.free_at
        flight.state = FlightState.BAGGAGE
        return baggage, flight

    @staticmethod
    def delay_flight(flight, delay=20):
        flight.arrival_time += timedelta(minutes=delay)
        return flight




class BaggageRepository:
    def __init__(self, airport_entity_handler=baggage_repository):
        self.handler = airport_entity_handler

    def get_baggages_for_airport(self, airport_code):
        return self.handler.get_active_baggages_for_airport(airport_code)


class FlightQueueFactory:
    @staticmethod
    def build_arrival_queue(flights):
        return deque(sorted(flights, key=lambda f: f.arrival_time))


class BaggageScheduleService:
    def __init__(self, flight_repo = FlightInstanceRepository, baggage_repo = BaggageRepository(), calculator=BaggageTimeCalculator, delay_time=20):
        self.flight_repo = flight_repo
        self.baggage_repo = baggage_repo
        self.calculator = calculator
        self.delay_time = delay_time

    def assign_baggage(self, window_minutes=120):
        # Fetch upcoming flights
        upcoming_flights = self.flight_repo.get_landed_flights()
        logger.info("Upcoming flights for baggage: %d", len(upcoming_flights))

        # Group flights by airport
        airport_to_flights = {}
        for flight in upcoming_flights:
            airport_to_flights.setdefault(flight.destination.code, []).append(flight)

        updated_flights = []

        # Assign baggage per airport
        for airport_code, flights in airport_to_flights.items():
            baggages = self.baggage_repo.get_baggages_for_airport(airport_code)
            flight_queue = FlightQueueFactory.build_arrival_queue(flights)

            # Assign baggages to flights
            for baggage in baggages:
                if not flight_queue:
                    break
                current_flight = flight_queue.popleft()
                baggage, updated_flight = self.calculator.assign_baggage_time(baggage, current_flight)
                baggage.save()
                updated_flights.append(updated_flight)
                FlightScheduleJob.schedule_baggage_close(flight=updated_flight)
                KafkaService().produce(message = f"Flight {flight.code} assigned with Baggage {flight.baggage.code} Airport {flight.destination.code} ")



            # Delay leftover flights
            while flight_queue:
                current_flight = flight_queue.popleft()
                updated_flights.append(self.calculator.delay_flight(current_flight, self.delay_time))

        self.flight_repo.update_all(updated_flights,['arrival_time','state','baggage'])
        logger.info("Baggage assigned/delayed for %d flights", len(updated_flights))
        return updated_flights
