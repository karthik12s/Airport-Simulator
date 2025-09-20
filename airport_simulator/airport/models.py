from django.db.models import TextField,CharField,FloatField,BooleanField,Model,ForeignKey,CASCADE, IntegerField, CompositePrimaryKey, DateTimeField, TextChoices, UniqueConstraint,SET_DEFAULT, TimeField



# Create your models here.
class Entity(TextChoices):
    BAGGAGE = 'BG', 'BAGGAGE_BELT',
    GATE = 'GT', 'GATE'
    
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
    airport = ForeignKey(Airport,on_delete=CASCADE)
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
    airport = ForeignKey(Airport,on_delete=CASCADE)
    length = IntegerField()
    material = CharField()
    free_at = DateTimeField(auto_now_add=True)
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
    free_at = DateTimeField(auto_now_add=True)
    terminal = ForeignKey(Terminal,on_delete=CASCADE)
    
    entity = CharField(
        choices=Entity.choices
    )
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
    code = CharField(primary_key=True)
    source = ForeignKey(Airport,on_delete=SET_DEFAULT,default="NA",related_name='source_aiport_code_instance')
    destination = ForeignKey(Airport,on_delete=SET_DEFAULT,default="NA")
    arrival_time = DateTimeField()
    departure_time = DateTimeField()
    scheduled_arrival_time = DateTimeField()
    scheduled_departure_time = DateTimeField()
    airline = ForeignKey(Airline,on_delete=SET_DEFAULT,default="NA")
    Aircraft = ForeignKey(Aircraft,on_delete=SET_DEFAULT,default="NA")
    domestic = BooleanField(default=True)
    active = BooleanField(default=True)
    gate = ForeignKey(AirportEntity,on_delete=SET_DEFAULT,default = None,related_name='source_aiport_gate_code')
    baggage = ForeignKey(AirportEntity,on_delete=SET_DEFAULT,default = None)
    take_off_runway = ForeignKey(Runway,on_delete=SET_DEFAULT,default = None,related_name='source_aiport_runway_code')
    landing_runway = ForeignKey(Runway,on_delete=SET_DEFAULT,default = None)
    approved = BooleanField(default = False)
    created_at = DateTimeField(auto_now_add=True)


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