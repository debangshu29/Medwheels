from django.contrib import admin
from .models import DriverLocation, Ride, Feedback, Hospital, Pricing

admin.site.register(DriverLocation)
admin.site.register(Ride)
admin.site.register(Feedback)
admin.site.register(Hospital)
admin.site.register(Pricing)
