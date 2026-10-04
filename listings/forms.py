from django.forms import ModelForm
from .models import Property


class PropertyForm(ModelForm):
    class Meta:
        model = Property
        fields = [
            "title",
            "description",
            "land_type",
            "district",
            "taluka",
            "village",
            "latitude",
            "longitude",
            "area_value",
            "area_unit",
            "price_inr",
            "contact_phone",
            "is_active",
        ]
