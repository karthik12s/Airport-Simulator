from ..models import Flight,FlightInstance
from datetime import datetime,timezone,timedelta


    
class FlightTimeCalculator:
    @staticmethod
    def compute_times(flight, current_time):
        # departure
        departure_date = current_time.date()
        if flight.departure_time <= current_time.time():
            departure_date += timedelta(days=1)
        departure_dt = datetime.combine(departure_date, flight.departure_time)

        # arrival
        if flight.arrival_time < flight.departure_time:
            arrival_dt = datetime.combine(departure_dt.date() + timedelta(days=1), flight.arrival_time)
        else:
            arrival_dt = datetime.combine(departure_dt.date(), flight.arrival_time)

        return departure_dt, arrival_dt


class FlightRepository:
    @staticmethod
    def get_upcoming_flights(current_time, window_minutes):
        window_end = current_time + timedelta(minutes=window_minutes)
        return Flight.objects.filter(
            departure_time__range=(current_time, window_end), active=True
        )

    


class FlightInstanceFactory:
    @staticmethod
    def create_instance(flight, departure_dt, arrival_dt):
        return FlightInstance(
            code=flight.code,
            source=flight.source,
            destination=flight.destination,
            departure_time=departure_dt,
            arrival_time=arrival_dt,
            scheduled_departure_time=departure_dt,
            scheduled_arrival_time=arrival_dt,
            airline=flight.airline,
            Aircraft=flight.Aircraft,
            domestic=flight.domestic,
            state="P",
        )


class FlightInstanceRepository:
    @staticmethod
    def save_all(instances):
        FlightInstance.objects.bulk_create(instances)

    @staticmethod
    def update_all(instances,attributes):
        FlightInstance.objects.bulk_update(instances, attributes)
    
    @staticmethod
    def get_scheduled_flight_codes(current_time):
        return set(
            FlightInstance.objects.filter(departure_time__gt=current_time)
            .values_list("code", flat=True)
        )
    
    @staticmethod
    def get_landed_flights():
        return FlightInstance.objects.filter(state__in = ['TI','L'])
    
    @staticmethod
    def get_upcoming_flights(comparision_time):
        return FlightInstance.objects.filter(
            departure_time__lt=comparision_time, state="A"
        )

    
    @staticmethod
    def update_pending_flights(current_time,window_minutes):
        window_end = current_time + timedelta(minutes=window_minutes)
        return FlightInstance.objects.filter(departure_time__range=(current_time, window_end),state = 'P').update(status='A')
        
    @staticmethod
    def get_flights(**filters):
        return FlightInstance.objects.filter(**filters)


class FlightSchedulerService:
    def __init__(self, repo=FlightRepository, instance_repo=FlightInstanceRepository, calculator=FlightTimeCalculator):
        self.repo = repo
        self.instance_repo = instance_repo
        self.calculator = calculator

    def schedule(self, window_minutes=360):
        current_time = datetime.now(timezone.utc)

        upcoming = self.repo.get_upcoming_flights(current_time, window_minutes)
        already_scheduled = self.instance_repo.get_scheduled_flight_codes(current_time)

        new_flights = [f for f in upcoming if f.code not in already_scheduled]

        instances = []
        for flight in new_flights:
            dep, arr = self.calculator.compute_times(flight, current_time)
            instances.append(FlightInstanceFactory.create_instance(flight, dep, arr))

        self.instance_repo.save_all(instances)
        return instances
    
    def update_flight_status(self,window_minutes = 120):
        current_time = datetime.now(timezone.utc)
        flights_updated = self.instance_repo.update_pending_flights(current_time,window_minutes)
        return flights_updated

