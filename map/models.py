# In map/models.py

from django.db import models
from django.contrib.auth import get_user_model
from uuid import uuid4
import uuid


from verify.models import Driver
User = get_user_model()

class DriverLocation(models.Model):
    driver = models.OneToOneField(Driver, on_delete=models.CASCADE, related_name='driver_location')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, db_index=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, db_index=True)
    location_name = models.CharField(max_length=255)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Location of {self.driver.username}"

class DriverRideLocationHistory(models.Model):
    driver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='location_history')
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    timestamp = models.DateTimeField(auto_now_add=True)

class Feedback(models.Model):
    ride = models.OneToOneField('map.Ride', on_delete=models.CASCADE, related_name='feedback')
    rating = models.DecimalField(max_digits=3, decimal_places=1, blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    selected_options = models.TextField(blank=True, null=True)  # New field to store selected options
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback for Ride {self.ride.id} - {self.rating} stars"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        # Call the original save method to ensure feedback is saved
        super().save(*args, **kwargs)

        # Update the driver's cumulative rating only if it's a new review
        if is_new and self.rating is not None:
            driver = self.ride.driver
            # Use F expressions to avoid race conditions
            from django.db.models import F
            from django.db.models.functions import Coalesce

            # Update total rating and count atomically
            driver.rating_total = Coalesce(F('rating_total'), 0.00) + self.rating
            driver.rating_count = Coalesce(F('rating_count'), 0) + 1
            driver.save(update_fields=['rating_total', 'rating_count'])


def generate_token():
    return uuid.uuid4().hex[:16]

class Ride(models.Model):
    driver = models.ForeignKey('verify.Driver', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pickup = models.CharField(max_length=255)
    drop = models.CharField(max_length=255)
    estimated_time = models.CharField(max_length=50, blank=True, null=True)
    estimated_distance = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_confirmed = models.BooleanField(default=False, db_index=True)
    token = models.CharField(max_length=32, unique=True, default=generate_token)
    pickup_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    pickup_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    drop_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    drop_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    fare = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ambulance_type = models.CharField(max_length=50, blank=True, null=True)
    code = models.CharField(max_length=4, unique=True, blank=True, null=True)
    is_verified = models.BooleanField(default=False, blank=True, null=True, db_index=True)
    is_completed = models.BooleanField(default=False, blank=True, null=True, db_index=True)
    payment_confirmed = models.BooleanField(default=False, blank=True, null=True)
    status = models.CharField(max_length=20, default='pending', blank=True, null=True)
    is_paid = models.BooleanField(default=False, blank=True, null=True)

    def __str__(self):
        return f"Ride from {self.pickup} to {self.drop}"

    def save(self, *args, **kwargs):
        if not self.pk and not self.code:
            self.code = self._generate_unique_code()
        super().save(*args, **kwargs)

    def _generate_unique_code(self):
        code = None
        while not code or Ride.objects.filter(code=code).exists():
            code = uuid4().hex[:4].upper()
        return code

class Hospital(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    latitude = models.DecimalField(max_digits=25, decimal_places=15)
    longitude = models.DecimalField(max_digits=25, decimal_places=15)
    website = models.URLField(max_length=400, blank=True, null=True)
    rating = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)

    def __str__(self):
        return self.name

class Pricing(models.Model):
    ambulance_type = models.CharField(max_length=50, unique=True, help_text="e.g. med_bls, med_als, med_icu")
    base_fare = models.DecimalField(max_digits=10, decimal_places=2, default=50.00)
    per_km_rate = models.DecimalField(max_digits=10, decimal_places=2, default=10.00)
    
    def __str__(self):
        return f"{self.ambulance_type} Pricing"