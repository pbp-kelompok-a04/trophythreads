from django.db import models
from django.conf import settings

class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorites'
)

product = models.ForeignKey('merchandise.Product', on_delete=models.CASCADE)
created_at = models.DateTimeField(auto_now_add=True)

class Meta:
    unique_together = ('user', 'product')
    ordering = ['-created_at']


def __str__(self):
    return f"Favorite(user={self.user}, product={self.product})"