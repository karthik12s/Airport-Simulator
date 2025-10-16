# airport/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler


def my_scheduled_task():
    from .flight_scheduler import FlightSchedulerService
    from .gate_assigner import GateScheduleService
    from .baggage_assigner import BaggageScheduleService
    from .ATCService import ATCService

    flight_scheduler = FlightSchedulerService()
    flight_scheduler.schedule(window_minutes=360)
    flight_scheduler.update_flight_status(window_minutes=120)
    gate_scheduler = GateScheduleService()
    gate_scheduler.assign_gates()

    baggage_scheduler = BaggageScheduleService()
    baggage_scheduler.assign_baggage()

    atc = ATCService()
    atc.start_ATC_scheduler()

    print("Scheduled task executed!")


def start():
    scheduler = BackgroundScheduler()
    # my_scheduled_task()
    scheduler.add_job(my_scheduled_task, "interval", seconds=300)  
    scheduler.start()
    return scheduler
