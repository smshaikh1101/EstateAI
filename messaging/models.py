from django.conf import settings
from django.db import models
from listings.models import Property


class Thread(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="buy_threads")
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sell_threads")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["property", "buyer", "seller"], name="unique_thread")
        ]

    def __str__(self):
        return f"Thread({self.property_id}) {self.buyer}->{self.seller}"


class Message(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
