from django.conf import settings
from django.db import models


class Property(models.Model):
    LAND_TYPES = [
        ("farm", "Farm Land"),
        ("residential", "Residential"),
        ("commercial", "Commercial"),
        ("industrial", "Industrial"),
        ("plot", "Plot"),
    ]

    AREA_UNITS = [
        ("sqft", "Sq Ft"),
        ("sq_m", "Sq Meter"),
        ("acre", "Acre"),
        ("hectare", "Hectare"),
        ("guntha", "Guntha"),
    ]

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="properties")

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    land_type = models.CharField(max_length=20, choices=LAND_TYPES)
    district = models.CharField(max_length=100)
    taluka = models.CharField(max_length=100, blank=True)
    village = models.CharField(max_length=100, blank=True)

    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    area_value = models.DecimalField(max_digits=12, decimal_places=2)
    area_unit = models.CharField(max_length=20, choices=AREA_UNITS, default="sqft")
    area_sq_m = models.FloatField(default=0.0)

    price_inr = models.IntegerField()
    contact_phone = models.CharField(max_length=20, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        v = float(self.area_value)
        if self.area_unit == "sqft":
            self.area_sq_m = v * 0.092903
        elif self.area_unit == "sq_m":
            self.area_sq_m = v
        elif self.area_unit == "acre":
            self.area_sq_m = v * 4046.8564224
        elif self.area_unit == "hectare":
            self.area_sq_m = v * 10000.0
        elif self.area_unit == "guntha":
            self.area_sq_m = v * 101.17141056
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.district})"


class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="property_images/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
