from django.db.models import TextField,CharField,FloatField,BooleanField,Model,ForeignKey,CASCADE, IntegerField, CompositePrimaryKey



# Create your models here.

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
    pk = CompositePrimaryKey('airport','code')

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

models_list = [Airport,Airline,ATC,Aircraft]