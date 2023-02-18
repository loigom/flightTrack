# https://stackoverflow.com/questions/39021159/django-template-send-two-arguments-to-template-tag

from django.utils import timezone
from datetime import datetime
from django import template

register = template.Library()

@register.simple_tag
def timestamp_to_aware_datetime(timestamp: int) -> datetime:
    if timestamp:
        return timezone.make_aware(datetime.fromtimestamp(timestamp))
