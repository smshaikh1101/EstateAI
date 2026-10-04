from django.conf import settings
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True)
    phone_verified = models.BooleanField(default=False)

    def trust_score(self) -> int:
        score = 0
        if self.user.email:
            score += 10
        if self.phone:
            score += 10
        if self.phone_verified:
            score += 20
        approved_docs = self.documents.filter(status="approved").count()
        score += min(60, approved_docs * 30)
        return min(100, score)

    def __str__(self):
        return f"Profile({self.user.username})"


class VerificationDocument(models.Model):
    DOC_TYPES = [
        ("id", "ID Proof"),
        ("land", "Land Document (7/12, Property Card etc.)"),
        ("other", "Other"),
    ]
    STATUS = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="verification_docs")
    doc_type = models.CharField(max_length=20, choices=DOC_TYPES)
    file = models.FileField(upload_to="verification_docs/")
    status = models.CharField(max_length=20, choices=STATUS, default="pending")
    note = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.user.username}:{self.doc_type}:{self.status}"
