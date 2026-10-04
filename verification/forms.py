from django import forms
from .models import VerificationDocument


class UploadDocForm(forms.ModelForm):
    class Meta:
        model = VerificationDocument
        fields = ["doc_type", "file"]
