from django.contrib import admin
from .models import Itinerary, ItineraryFlight, Airline

class ItineraryFlightAdmin(admin.ModelAdmin):
    exclude = ItineraryFlight.ADMIN_EXCLUDED

regular_models = (
    Itinerary,
    Airline
)

admin.site.register(regular_models)
admin.site.register(ItineraryFlight, ItineraryFlightAdmin)
