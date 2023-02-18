from django.db import models
from django.utils import timezone
from .flightradar import find_flight
from datetime import datetime


class Itinerary(models.Model):
    name = models.TextField()

    @property
    def done(self) -> bool:
        flights = ItineraryFlight.objects.filter(itinerary=self)
        landed_flights = flights.filter(status=ItineraryFlight.LANDED)
        return len(flights) == len(landed_flights)

    @staticmethod
    def update_itineraries() -> None:
        for itinerary in Itinerary.objects.all():
            now = timezone.now()
            if not itinerary.done:
                flights = ItineraryFlight.objects.filter(itinerary=itinerary).order_by("number_in_itinerary")
                for flight in flights:
                    if flight.status != ItineraryFlight.LANDED and flight.scheduled_takeoff <= now:
                        flight.update()
                        break

    def __str__(self) -> str:
        return self.name

class Airline(models.Model):
    name = models.TextField()
    icao = models.TextField()

    def __str__(self) -> str:
        return self.name

class ItineraryFlight(models.Model):
    ADMIN_EXCLUDED = (
        "actual_takeoff_ts",
        "actual_landed_ts",
        "status",
        "last_updated_ts",
        "map_link"
    )

    itinerary = models.ForeignKey(Itinerary, on_delete=models.PROTECT)
    airline = models.ForeignKey(Airline, on_delete=models.PROTECT)
    number_in_itinerary = models.IntegerField()
    plane_number = models.TextField()
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

    def update(self) -> None:
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

        if self.actual_landed_ts:
            self.status = self.LANDED
        elif self.actual_takeoff_ts:
            self.status = self.IN_FLIGHT

        self.save(force_update=True)

    def __str__(self) -> str:
        return f"[{self.itinerary}] {self.airline} {self.plane_number} ({self.number_in_itinerary})"
