from django.db.models import TextField,CharField,FloatField,BooleanField,Model,ForeignKey,CASCADE, IntegerField, CompositePrimaryKey, DateTimeField, TextChoices, UniqueConstraint,SET_DEFAULT, TimeField, AutoField
from django.utils import timezone



# Create your models here.
class Entity(TextChoices):
    BAGGAGE = 'BG', 'BAGGAGE_BELT',
    GATE = 'GT', 'GATE'
    
class FlightState (TextChoices):
        PENDING = "P" , "PENDING",
        ACCEPTED = 'A', "ACCEPTED",
        REJECTED = 'R', 'REJECTED',
        GATE = 'G', "GATE",
        PUSHBACK = 'PU', "PUSHBACK",
        TAXIOUT = 'TO', 'TAXIOUT',
        TAKEOFF = 'T', 'TAKEOFF',
        AIR = 'AI', 'AIR',
        LANDING = 'L','LANDING',
        TAXIIN = 'TI' , 'TAXIIN',
        BAGGAGE = 'B' , 'BAGGAGE',
        CLOSED = 'C', 'CLOSED',
        CANCELLED = 'CA','CANCELLED',
        DIVERTED = 'DIV' , 'DIVERTED',
        INAPPROACH = 'AP','INAPPROACH'
class Airport(Model):
    name = TextField()
    code = CharField(primary_key = True)
    latitude = FloatField()
    longitude = FloatField()
    active = BooleanField(default = True)
    domestic = BooleanField(default = True)
    def __str__(self):
        return "Airport Model" + self.code
    
class Airline(Model):
    code = CharField(primary_key=True)
    name = CharField()
    active = BooleanField(default = True)

class Terminal(Model):
    airport = ForeignKey(Airport,on_delete=CASCADE, related_name='terminals')
    code = CharField()
    active = BooleanField(default = True)
    capacity = IntegerField()
    domestic = BooleanField(default = True)
    class Meta:
        constraints = [
            UniqueConstraint(fields = ['code','airport'],name = "unique_terminal")
        ]

class ATC(Model):
    airport = ForeignKey(Airport,on_delete=CASCADE)
    frequency = FloatField()
    active = BooleanField(default = True)
    number = IntegerField(default = 1)

class Aircraft(Model):
    name = CharField(primary_key=True)
    manufacturer = CharField()
    takeoff_req = IntegerField()
    landing_req = IntegerField()
    capacity = IntegerField()


class Runway(Model):
    airport = ForeignKey(Airport,on_delete=CASCADE, related_name='runways')
    length = IntegerField()
    material = CharField()
    free_at = DateTimeField(default=timezone.now)
    number_1 = CharField()
    number_2 = CharField()
    active = BooleanField(default = True)
    class Meta:
        constraints = [
            UniqueConstraint(fields = ['airport','number_1','number_2'],name = "unique_runway")
        ]

class AirportEntity(Model):
    code  = CharField()
    capacity = IntegerField()
    free_at = DateTimeField(default=timezone.now)
    terminal = ForeignKey(Terminal,on_delete=CASCADE, related_name='airport_entity')
    active = BooleanField(default=True)
    entity = CharField(
        choices=Entity.choices
    )
    flightId = CharField(default='')
    class Meta:
        constraints = [
            UniqueConstraint(fields = ['terminal','code'],name = "unique_entity")
        ]

class AirlineAcceptance(Model):
    airport = ForeignKey(Airport,on_delete=CASCADE)
    airline = ForeignKey(Airline,on_delete=CASCADE)
    class Status (TextChoices):
        PENDING = "P" , "PENDING",
        ACCEPTED = 'A', "ACCEPTED",
        REJECTED = 'R', 'REJECTED'
    state = CharField(choices=Status.choices,default='P')

class Flight(Model):
    code = CharField(primary_key=True)
    source = ForeignKey(Airport,on_delete=SET_DEFAULT,default="NA",related_name='source_aiport_code')
    destination = ForeignKey(Airport,on_delete=SET_DEFAULT,default="NA")
    arrival_time = TimeField()
    departure_time = TimeField()
    airline = ForeignKey(Airline,on_delete=SET_DEFAULT,default="NA")
    Aircraft = ForeignKey(Aircraft,on_delete=SET_DEFAULT,default="NA")
    domestic = BooleanField(default=True)
    active = BooleanField(default=True)

class FlightInstance(Model):
    id = AutoField(primary_key=True)
    code = CharField()
    source = ForeignKey(Airport,on_delete=SET_DEFAULT,default="NA",related_name='source_aiport_code_instance')
    destination = ForeignKey(Airport,on_delete=SET_DEFAULT,default="NA")
    arrival_time = DateTimeField()
    departure_time = DateTimeField()
    scheduled_arrival_time = DateTimeField()
    scheduled_departure_time = DateTimeField()
    airline = ForeignKey(Airline,on_delete=SET_DEFAULT,default="NA")
    Aircraft = ForeignKey(Aircraft,on_delete=SET_DEFAULT,default="NA")
    domestic = BooleanField(default=True)
    gate = ForeignKey(AirportEntity,on_delete=SET_DEFAULT,default = None,null=True,related_name='source_aiport_gate_code')
    baggage = ForeignKey(AirportEntity,on_delete=SET_DEFAULT,default = None,null=True,related_name='source_aiport_baggage_code')
    take_off_runway = ForeignKey(Runway,on_delete=SET_DEFAULT,default = None,null=True,related_name='source_aiport_runway_code')
    landing_runway = ForeignKey(Runway,on_delete=SET_DEFAULT,default = None,null=True,related_name='destination_aiport_runway_code')
    
    state = CharField(
        choices= FlightState.choices,
        default='P'
    )
    created_at = DateTimeField(default=timezone.now)


class AirportEntityLogging(Model):
    entity = CharField(
        choices=Entity.choices
    )
    flight_instance = ForeignKey(FlightInstance,on_delete=SET_DEFAULT,default="NA")
    assigned_time = DateTimeField()
    valid_till = DateTimeField()
    class Action(TextChoices):
        ALLOTED = 'A','ALLOTED',
        CLOSED = 'C' , 'CLOSED',
        REVOKED = 'R', 'REVOKED'
    action = CharField(
        choices=Action.choices
    )

models_list = [Airport,Airline,ATC,Aircraft,Runway,AirportEntity,Terminal,AirlineAcceptance,Flight,FlightInstance,AirportEntityLogging]