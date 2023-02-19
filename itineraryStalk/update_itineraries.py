# https://stackoverflow.com/questions/8047204/how-to-have-a-python-script-for-a-django-app-that-accesses-models-without-using

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'itineraryStalk.settings')
import django
django.setup()

from base.models import Itinerary
from time import sleep
from django.conf import settings

while True:
    print("Updating...")

    Itinerary.update_itineraries()

    print("Updated")

    sleep(settings.FLIGHTRADAR_FETCH_INTERVAL_SECONDS)
