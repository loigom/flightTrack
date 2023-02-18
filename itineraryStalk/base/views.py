from django.shortcuts import render
from .models import Itinerary

itineraries = [
    {
        "name": "Australia",
        "flights": [
            {"name": "123"},
            {"name": "345"}
        ]
    },
    {
        "name": "Eesti",
        "flights": [
            {"name": "aaa"},
            {"name": "aaa"}
        ]
    }
]

ctx = {
    "itineraries": itineraries
}


def home(request):
    Itinerary.update_itineraries()
    return render(request, 'home.html', {"itineraries": itineraries})
