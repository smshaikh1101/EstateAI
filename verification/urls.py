from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="verify_dashboard"),
    path("upload/", views.upload_doc, name="verify_upload"),
]
