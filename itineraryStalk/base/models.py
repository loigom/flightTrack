from django.db import models
from django.utils import timezone
from .flightradar import find_flight
from datetime import datetime
from typing import List


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
            if flight.scheduled_takeoff <= now:
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

class ItineraryFlight(models.Model):
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE)
    airline = models.ForeignKey(Airline, on_delete=models.CASCADE)
    number_in_itinerary = models.IntegerField()
    plane_number = models.TextField()
    departing_location = models.TextField()
    arriving_location = models.TextField()
    scheduled_takeoff = models.DateTimeField()
    scheduled_landing = models.DateTimeField()

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

        try:
            flight = find_flight(self.plane_number, self.airline.icao)
        except Exception as e:
            print("Encountered exception when attempting to request flight.", e)
            return

        if not flight:
            return

        now = datetime.now().timestamp()
        self.last_updated_ts = int(now)

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

        print(flight.time_details)
        print(f"Updated {str(self)}")

        return self.status == self.LANDED

    @property
    def takeoff_actual_datetime(self) -> datetime:
        if self.actual_takeoff_ts:
            return timezone.make_aware(datetime.fromtimestamp(self.actual_takeoff_ts))

    @property
    def landing_actual_datetime(self) -> datetime:
        if self.actual_landed_ts:
            return timezone.make_aware(datetime.fromtimestamp(self.actual_landed_ts))

    @property
    def readable_eta(self) -> str:
        now = datetime.now().timestamp()
        if self.eta_landing_ts and now < self.eta_landing_ts:
            seconds_until_land = int(self.eta_landing_ts - now)
            minutes_until_land = seconds_until_land // 60
            hours_until_land = minutes_until_land // 60
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
