from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("my/", views.my_listings, name="my_listings"),
    path("nearby/", views.nearby_page, name="nearby_page"),

    path("properties/new/", views.property_create, name="property_create"),
    path("properties/<int:pk>/", views.property_detail, name="property_detail"),
    path("properties/<int:pk>/edit/", views.property_edit, name="property_edit"),
]
