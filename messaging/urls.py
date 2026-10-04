from django.urls import path
from . import views

urlpatterns = [
    path("", views.thread_list, name="thread_list"),
    path("start/<int:property_id>/", views.start_thread, name="start_thread"),
    path("<int:thread_id>/", views.thread_detail, name="thread_detail"),
]
