import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from merchandiseApp.models import Merchandise

class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} by {self.user}"


class OrderItem(models.Model):
    id = models.BigAutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Merchandise, on_delete=models.CASCADE)
    purchased_at = models.DateField(default=timezone.localdate)

    def __str__(self):
        return f"{self.product.name} (Order {self.order_id})"


class Review(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Merchandise, on_delete=models.CASCADE, related_name='reviews', db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    body = models.TextField()
    purchased_at = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['product', 'user'], name='unique_user_review_per_product')
        ]
        indexes = [
            models.Index(fields=['product', 'deleted', '-created_at']),
            models.Index(fields=['product', 'rating']),
        ]
        ordering = ['-created_at']

    def clean(self):
        if not (1 <= int(self.rating) <= 5):
            raise ValidationError("Rating harus 1–5.")

    def save(self, *args, **kwargs):
        if not self.purchased_at:
            oi = (
                OrderItem.objects
                .filter(order__user=self.user, product=self.product)
                .order_by('-purchased_at')
                .first()
            )
            if oi:
                self.purchased_at = oi.purchased_at
        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        self.deleted = True
        self.save(update_fields=['deleted'])

    @property
    def is_positive(self):
        return self.rating >= 4

    @property
    def is_critical(self):
        return self.rating <= 2
