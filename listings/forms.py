from django import forms
from django.forms import ModelForm
from .models import Property
from .locations import DISTRICTS

DISTRICT_CHOICES = [("", "Select district")] + [(d, d) for d in DISTRICTS]


class PropertyForm(ModelForm):
    district = forms.CharField(widget=forms.Select(choices=DISTRICT_CHOICES))

    class Meta:
        model = Property
        fields = [
            "title","description","land_type",
            "district","taluka","village",
            "latitude","longitude",
            "area_value","area_unit",
            "price_inr","contact_phone",
            "is_active",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["taluka"].widget.attrs.update(
            {"list": "taluka-list", "autocomplete": "off", "placeholder": "Start typing taluka..."}
        )
