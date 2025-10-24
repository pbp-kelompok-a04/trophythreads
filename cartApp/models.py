# cartApp/models.py
import uuid
from django.db import models
from django.conf import settings
from django.db.models import F
from merchandiseApp.models import Merchandise

User = settings.AUTH_USER_MODEL

class Cart(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=255, null=True, blank=True)

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
    product_name = models.CharField(max_length=255, null=True, blank=True)
    product_price = models.IntegerField(null=True, blank=True)
    product_thumbnail = models.URLField(null=True, blank=True)
    product_stock = models.IntegerField(null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    selected = models.BooleanField(default=True)

    def line_total(self):
        price = self.product.price if self.product else (self.product_price or 0)
        return self.quantity * price

    def __str__(self):
        name = self.product.name if self.product else (self.product_name or 'Unknown')
        return f"{name} x{self.quantity}"

class Purchase(models.Model):
    order_token = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="purchases")
    product = models.ForeignKey(
        "merchandiseApp.Merchandise",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="purchases"
    )

    product_name = models.CharField(max_length=255, blank=True)
    product_price = models.IntegerField(default=0)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["user", "product"]),
            models.Index(fields=["product"]),
            models.Index(fields=["order_token"]),
        ]

    def line_total(self):
        return (self.product_price or (self.product.price if self.product else 0)) * self.quantity

    def __str__(self):
        name = self.product.name if self.product else (self.product_name or "Unknown")
        return f"Purchase {self.order_token} - {name} x{self.quantity}"
