from django.contrib import admin
from .models import Itinerary, ItineraryFlight, Airline

class ItineraryFlightAdmin(admin.ModelAdmin):
    exclude = (
        "actual_takeoff_ts",
        "actual_landed_ts",
        "status",
        "last_updated_ts",
        "map_link",
        "eta_landing_ts"
    )

regular_models = (
    Itinerary,
    Airline
)

admin.site.register(regular_models)
admin.site.register(ItineraryFlight, ItineraryFlightAdmin)
