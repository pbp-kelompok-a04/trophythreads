# cartApp/models.py
import uuid
from django.db import models
from django.conf import settings
from merchandiseApp.models import Merchandise

User = settings.AUTH_USER_MODEL

class Cart(models.Model):
    """
    Cart can belong to a logged-in user OR be tied to a session_key (guest).
    """
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.user:
            return f"Cart(user={self.user})"
        return f"Cart(session={self.session_key})"

    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    def subtotal(self):
        return sum(item.line_total() for item in self.items.filter(selected=True))


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Merchandise, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    selected = models.BooleanField(default=True)
    variant = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def line_total(self):
        return self.quantity * self.product.price

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"
