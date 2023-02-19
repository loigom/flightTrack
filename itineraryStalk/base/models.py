from django.db import models
from django.utils import timezone
from django.conf import settings
from .flightradar import find_flight
from datetime import datetime, timedelta
from typing import List
from .templatetags.tags import progress_bar_value


class Itinerary(models.Model):
    name = models.TextField()
    done = models.BooleanField(default=False)

    @property
    def unfinished_flights(self) -> List["ItineraryFlight"]:
        return [flight for flight in self.flights if flight.status != ItineraryFlight.LANDED]

    @property
    def flights(self) -> List["ItineraryFlight"]:
        return ItineraryFlight.objects.filter(itinerary=self).order_by("number_in_itinerary")
    
    def update(self) -> None:
        now = timezone.now()
        unfinished_flights = self.unfinished_flights

        for flight in unfinished_flights:
            flight_utc = flight.scheduled_takeoff - timedelta(hours=flight.departure_location.timezone_utc_offset)
            now_utc = now - timedelta(hours=settings.UTC_OFFSET)
            
            if flight_utc <= now_utc:
                flight_completed = flight.update()
                if flight_completed and len(unfinished_flights) == 1:
                    self.done = True
                    self.save(force_update=True)

    def __str__(self) -> str:
        return self.name

    @staticmethod
    def update_itineraries() -> None:
        for itinerary in Itinerary.objects.all():
            itinerary.update()

class Airline(models.Model):
    name = models.TextField()
    icao = models.TextField()

    def __str__(self) -> str:
        return self.name

class Location(models.Model):
    name = models.TextField()
    timezone_utc_offset = models.IntegerField()

    def __str__(self) -> str:
        return f"{self.name} [UTC{self.timezone_utc_offset}]"

class ItineraryFlight(models.Model):
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE)
    airline = models.ForeignKey(Airline, on_delete=models.CASCADE)
    number_in_itinerary = models.IntegerField()
    plane_number = models.TextField()
    scheduled_takeoff = models.DateTimeField()
    scheduled_landing = models.DateTimeField()
    departure_location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name="departure_locations")
    arrival_location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name="arrival_locations")

    # The below attributes are hidden from the admin page. Back-end modifying only.
    eta_landing_ts = models.IntegerField(null=True, blank=True)
    actual_takeoff_ts = models.IntegerField(null=True, blank=True)
    actual_landed_ts = models.IntegerField(null=True, blank=True)
    last_updated_ts = models.IntegerField(null=True, blank=True)

    NOT_DEPARTED = "NONE"
    IN_FLIGHT = "FLYING"
    LANDED = "LANDED"
    STATUSES = (
        (NOT_DEPARTED, "Not departed"),
        (IN_FLIGHT, "Flying"),
        (LANDED, "Landed")
    )
    status = models.TextField(choices=STATUSES, default=NOT_DEPARTED)
    map_link = models.URLField(null=True, blank=True)

    def update(self) -> bool:
        print(f"Updating {str(self)}")

        if self.status == self.LANDED:
            return

        # TODO: backup icao's. aka: malta airlines or ryanairs? could be either
        try:
            flight = find_flight(self.plane_number, self.airline.icao)
        except Exception as e:
            print("Encountered exception when attempting to request flight.", e)
            return

        now = datetime.now().timestamp()
        self.last_updated_ts = int(now)

        if not flight:
            if self.status == self.IN_FLIGHT and progress_bar_value(self) >= 96:
                self.status = self.LANDED
                self.actual_landed_ts = now
            else:
                return

        if flight:
            self.map_link = f"https://www.flightradar24.com/{self.plane_number}/{flight.id}"

            if flight.time_details["real"]["departure"]:
                self.actual_takeoff_ts = flight.time_details["real"]["departure"]
            if flight.time_details["real"]["arrival"]:
                self.actual_landed_ts = flight.time_details["real"]["arrival"]
            if flight.time_details['estimated']["arrival"]:
                self.eta_landing_ts = flight.time_details['estimated']["arrival"]

            if self.actual_landed_ts:
                self.status = self.LANDED
            elif self.actual_takeoff_ts:
                self.status = self.IN_FLIGHT

        self.save(force_update=True)

        return self.status == self.LANDED

    @property
    def readable_eta(self) -> str:
        if self.status == self.LANDED:
            return "Landed!"

        now = datetime.now().timestamp()
        if self.eta_landing_ts and now < self.eta_landing_ts:
            seconds_until_land = int(self.eta_landing_ts - now)
            minutes_until_land = seconds_until_land / 60
            hours_until_land = minutes_until_land / 60
            return f"In {int(hours_until_land)} hours, {int(minutes_until_land % 60)} minutes"

    @property
    def minutes_since_last_update(self) -> str:
        if self.last_updated_ts:
            return f"{int((datetime.now().timestamp() - self.last_updated_ts) / 60)} minutes ago"

    @property
    def full_name(self) -> str:
        return f"{self.airline} {self.plane_number}"

    def __str__(self) -> str:
        return f"[{self.itinerary}] {self.airline} {self.plane_number} ({self.number_in_itinerary})"
