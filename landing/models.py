from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from datetime import timedelta


class EmailVerificationToken(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="verification_token"
    )
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return now() < self.created_at + timedelta(minutes=15)
