from django.shortcuts import render
from django.http import HttpResponse
from .models import Airport

# Create your views here.

def home(request):
    print(Airport.objects.all())
    return HttpResponse("abc")