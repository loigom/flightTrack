from django.db import models
from .flightradar import find_flight


class Itinerary(models.Model):
    name = models.TextField()

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
        "last_updated_ts"
    )

    itinerary = models.ForeignKey(Itinerary, on_delete=models.PROTECT)
    airline = models.ForeignKey(Airline, on_delete=models.PROTECT)
    number_in_itinerary = models.IntegerField()
    plane_number = models.TextField()
    estimated_takeoff = models.DateTimeField()
    estimated_landing = models.DateTimeField()

    # The below attributes are hidden from the admin page. Back-end modifying only.
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

    def update(self) -> None:
        flight = find_flight(self.plane_number, self.airline.icao)

        if not flight:
            return

        

        self.save(force_update=True)

    def __str__(self) -> str:
        return f"[{self.itinerary}] {self.airline} {self.plane_number} ({self.number_in_itinerary})"
