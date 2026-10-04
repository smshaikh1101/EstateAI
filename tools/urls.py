from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="tools_index"),
    path("walk-area/", views.walk_area, name="tools_walk_area"),
]
