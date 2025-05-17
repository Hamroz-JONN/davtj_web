from django.db import models
from django.contrib.auth.models import User

class ExtendedUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    strava_id = models.IntegerField(null=False, unique=True)

    def __str__(self) -> str:
        return f'Extd-{self.user}'
    
