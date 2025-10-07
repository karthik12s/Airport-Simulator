from apscheduler.schedulers.background import BackgroundScheduler
from ..models import FlightInstance,FlightState
from datetime import datetime,timezone,timedelta
from ..services.kafka_service import KafkaService

class FlightScheduleJob():
    _background_scheduler = None
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FlightScheduleJob, cls).__new__(cls)
            cls._background_scheduler = BackgroundScheduler()
            cls._background_scheduler.start()
        return cls._instance
    @staticmethod
    def trigger_push_back(flight):
        flight = FlightInstance.objects.filter(id = flight.id).first()
        if flight.state in FlightState.GATE and flight.departure_time <= datetime.now(timezone.utc):
            flight.state = FlightState.PUSHBACK
            flight.save()
            KafkaService.produce(message = f"Flight {flight.code} Requesting Pushback clearance from Gate {flight.gate.code} ")

    def trigger_takeoff(flight):
        flight = FlightInstance.objects.filter(id = flight.id).first()
        if flight.state in FlightState.TAXIOUT and flight.departure_time <= datetime.now(timezone.utc):
            flight.state = FlightState.AIR
            flight.save()
            KafkaService.produce(message = f"Flight {flight.code} Taking off from Runway {flight.take_off_runway.number_1} Airport {flight.source.code} ")
    
    def trigger_landing(flight):
        flight = FlightInstance.objects.filter(id = flight.id).first()
        print(flight,flight.state,flight.departure_time,datetime.now(timezone.utc))
        if flight.state == FlightState.INAPPROACH and flight.arrival_time <= datetime.now(timezone.utc):
            flight.state = FlightState.TAXIOUT
            flight.save()
            KafkaService.produce(message = f"Flight {flight.code} Landed on Runway {flight.landing_runway.number_1} Airport {flight.destination.code} ")
    
    def trigger_landing(flight):
        flight = FlightInstance.objects.filter(id = flight.id).first()
        if flight.state == FlightState.BAGGAGE and flight.arrival_time <= datetime.now(timezone.utc):
            flight.state = FlightState.CLOSED
            flight.save()
            KafkaService.produce(message = f"Flight {flight.code} Taking off from Runway {flight.take_off_runway.number_1} ")
    
    def trigger_baggage_close(flight):
        flight = FlightInstance.objects.filter(id = flight.id).first()
        print(flight,flight.state,flight.departure_time,datetime.now(timezone.utc))
        if flight.state == FlightState.INAPPROACH and flight.arrival_time <= datetime.now(timezone.utc):
            flight.state = FlightState.TAXIOUT
            flight.save()
            KafkaService.produce(message = f"Flight {flight.code} Cycle has been completed ")
    
    @staticmethod
    def schedule_push_back(flights):
        print("inside schedule pushback",flights)
        for flight in flights:
            print(flight)
            print(flight.departure_time)
            t = BackgroundScheduler()
            # t.add_job(FlightScheduleJob.trigger_push_back,'date',run_date = flight.departure_time,args=[flight])
            print(FlightScheduleJob._background_scheduler)
            FlightScheduleJob._background_scheduler.add_job(FlightScheduleJob.trigger_push_back,'date',run_date = datetime.now()+timedelta(seconds=10),args=[flight])

    @staticmethod
    def schedule_takeoff(flight):
        FlightScheduleJob._background_scheduler.add_job(FlightScheduleJob.trigger_takeoff,'date',run_date = flight.departure_time,args=[flight])

    @staticmethod
    def schedule_landing(flight):
        FlightScheduleJob._background_scheduler.add_job(FlightScheduleJob.trigger_landing,'date',run_date = flight.arrival_time,args=[flight])

    @staticmethod
    def schedule_baggage_close(flight):
        FlightScheduleJob._background_scheduler.add_job(FlightScheduleJob.trigger_baggage_close,'date',run_date = flight.arrival_time,args=[flight])
