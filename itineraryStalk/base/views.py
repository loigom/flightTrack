from django.shortcuts import render
from .models import Itinerary


def home(request):
    Itinerary.update_itineraries()
    return render(request, 'home.html', {"itineraries": Itinerary.objects.all()})
