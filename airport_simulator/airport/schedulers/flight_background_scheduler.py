from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from django.db import transaction

from ..models import FlightInstance, FlightState
from ..services.kafka_service import KafkaService


class FlightScheduleJob:
    
    _instance = None
    _scheduler = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._scheduler = BackgroundScheduler()
            cls._scheduler.start()
        return cls._instance



    @staticmethod
    def _get_flight(flight_id):
        return FlightInstance.objects.filter(id=flight_id).first()
    
    @staticmethod
    def _get_all_flights(state):
        return FlightInstance.objects.filter(state=state)

    @staticmethod
    def _produce_event(message: str):
        try:
            KafkaService().produce(message=message)
        except Exception as e:
            print(f"[Kafka Error] {e}")

    

    @staticmethod
    def _trigger_pushback(flight_id):
        flight = FlightScheduleJob._get_flight(flight_id)
        if not flight:
            return
        if flight.state == FlightState.GATE and flight.departure_time <= datetime.now(timezone.utc):
            with transaction.atomic():
                flight.state = FlightState.PUSHBACK
                flight.save(update_fields=["state"])
            FlightScheduleJob._produce_event(
                f"Flight {flight.code} requesting pushback clearance from Gate {flight.gate.code}"
            )
        FlightScheduleJob._trigger_pushback_all()
    @staticmethod
    def _trigger_pushback_all():
        flights = FlightScheduleJob._get_all_flights(FlightState.GATE)
        if not flights:
            return
        for flight in flights:
            if flight.state == FlightState.GATE and flight.departure_time <= datetime.now(timezone.utc):
                with transaction.atomic():
                    flight.state = FlightState.PUSHBACK
                    flight.save(update_fields=["state"])
                FlightScheduleJob._produce_event(
                    f"Flight {flight.code} requesting pushback clearance from Gate {flight.gate.code}"
                )

    @staticmethod
    def _trigger_takeoff(flight_id):
        flight = FlightScheduleJob._get_flight(flight_id)
        if not flight:
            return
        if flight.state == FlightState.TAXIOUT and flight.departure_time <= datetime.now(timezone.utc):
            with transaction.atomic():
                flight.state = FlightState.AIR
                flight.save(update_fields=["state"])
            FlightScheduleJob._produce_event(
                f"Flight {flight.code} taking off from Runway {flight.take_off_runway.number_1} "
                f"at Airport {flight.source.code}"
            )

    @staticmethod
    def _trigger_landing(flight_id):
        flight = FlightScheduleJob._get_flight(flight_id)
        if not flight:
            return
        if flight.state == FlightState.INAPPROACH and flight.arrival_time <= datetime.now(timezone.utc):
            with transaction.atomic():
                flight.state = FlightState.TAXIOUT
                flight.save(update_fields=["state"])
            FlightScheduleJob._produce_event(
                f"Flight {flight.code} landed on Runway {flight.landing_runway.number_1} "
                f"at Airport {flight.destination.code}"
            )

    @staticmethod
    def _trigger_baggage_close(flight_id):
        flight = FlightScheduleJob._get_flight(flight_id)
        if not flight:
            return
        if flight.state == FlightState.BAGGAGE and flight.arrival_time <= datetime.now(timezone.utc):
            with transaction.atomic():
                flight.state = FlightState.CLOSED
                flight.save(update_fields=["state"])
            FlightScheduleJob._produce_event(
                f"Flight {flight.code} has completed its cycle at Airport {flight.destination.code}"
            )

    
    @classmethod
    def schedule_pushback(cls, flights):
        """Schedule pushback clearance for a list of flights."""
        for flight in flights:
            run_time = flight.departure_time
            cls._scheduler.add_job(
                cls._trigger_pushback,
                "date",
                run_date=flight.departure_time,
                args=[flight.id],
                id=f"pushback_{flight.id}",
                replace_existing=True,
            )
            FlightScheduleJob._produce_event(f"[Scheduler] Pushback job scheduled for {flight.code} at {run_time}")

    @classmethod
    def schedule_takeoff(cls, flight):
        cls._scheduler.add_job(
            cls._trigger_takeoff,
            "date",
            run_date= flight.departure_time,
            args=[flight.id],
            id=f"takeoff_{flight.id}",
            replace_existing=True,
        )
        FlightScheduleJob._produce_event(f"[Scheduler] Takeoff scheduled for {flight.code} at {flight.departure_time}")


    @classmethod
    def schedule_landing(cls, flight):
        cls._scheduler.add_job(
            cls._trigger_landing,
            "date",
            run_date=flight.arrival_time,
            args=[flight.id],
            id=f"landing_{flight.id}",
            replace_existing=True,
        )
        FlightScheduleJob._produce_event(f"[Scheduler] Landing scheduled for {flight.code} at {flight.arrival_time}")

    @classmethod
    def schedule_baggage_close(cls, flight):
        cls._scheduler.add_job(
            cls._trigger_baggage_close,
            "date",
            run_date=flight.arrival_time,
            args=[flight.id],
            id=f"baggage_close_{flight.id}",
            replace_existing=True,
        )
        FlightScheduleJob._produce_event(f"[Scheduler] Baggage closed scheduled for {flight.code} at {flight.arrival_time}")


