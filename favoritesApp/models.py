import uuid
from django.db import models
from django.contrib.auth import get_user_model
from merchandiseApp.models import Merchandise

User = get_user_model()

class Favorite(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    merchandise = models.ForeignKey(Merchandise, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'merchandise')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} ❤️ {self.merchandise.name}"
