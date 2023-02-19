# https://stackoverflow.com/questions/39021159/django-template-send-two-arguments-to-template-tag

from django.utils import timezone
from django.conf import settings
from datetime import datetime, timedelta
from django import template

register = template.Library()

@register.simple_tag
def timestamp_to_aware_datetime(timestamp: int) -> datetime:
    if timestamp:
        return timezone.make_aware(datetime.fromtimestamp(timestamp))


@register.simple_tag
def progress_bar_value(flight) -> int:
    if flight.status == flight.LANDED:
        return 100

    if flight.eta_landing_ts and flight.actual_takeoff_ts:
        now = datetime.now().timestamp()
        total_seconds_in_flight = flight.eta_landing_ts - flight.actual_takeoff_ts
        seconds_in_flight = now - flight.actual_takeoff_ts
        percentage = int(seconds_in_flight / total_seconds_in_flight * 100)
        return percentage if percentage < 100 else 100


@register.simple_tag
def progress_bar_classes(value: int) -> str:
    if value == 100:
        return "progress-bar progress-bar-striped bg-success"
    return "progress-bar progress-bar-striped progress-bar-animated"


@register.simple_tag
def server_timezone_string() -> str:
    return settings.TIME_ZONE


@register.simple_tag
def location_datetime_to_server_timezone(location, dtime) -> datetime:
    dif = settings.UTC_OFFSET - location.timezone_utc_offset
    return dtime + timedelta(hours=dif)
