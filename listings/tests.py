import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import translation
from listings.models import Property


@pytest.mark.django_db
def test_home_page(client):
    with translation.override("en"):
        resp = client.get(reverse("home"))
    assert resp.status_code == 200


@pytest.mark.django_db
def test_create_property_requires_login(client):
    with translation.override("en"):
        resp = client.get(reverse("property_create"))
    assert resp.status_code == 302


@pytest.mark.django_db
def test_logged_in_can_create_property(client):
    u = User.objects.create_user(username="seller1", password="pass12345")
    client.login(username="seller1", password="pass12345")

    with translation.override("en"):
        url = reverse("property_create")

    resp = client.post(
        url,
        data={
            "title": "Test Plot",
            "description": "Nice plot",
            "land_type": "plot",
            "district": "Pune",
            "taluka": "Haveli",
            "village": "TestVillage",
            "latitude": "18.5204",
            "longitude": "73.8567",
            "area_value": "10",
            "area_unit": "guntha",
            "price_inr": "1000000",
            "contact_phone": "9999999999",
            "is_active": "on",
        },
        follow=True,
    )
    assert resp.status_code == 200
    assert Property.objects.filter(title="Test Plot").exists()
