from django.shortcuts import render
from .models import Itinerary


def home(request):
    return render(request, 'home.html', {"itineraries": Itinerary.objects.all()})
