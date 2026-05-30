from django.contrib import admin
from .models import CustomUser, Driver

admin.site.register(CustomUser)
admin.site.register(Driver)
