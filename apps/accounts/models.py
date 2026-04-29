from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model. Kept thin on purpose — extend here rather than
    patching auth.User later when the schema is harder to change.
    """
    pass


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True)

    def __str__(self):
        return f"Profile({self.user.username})"
