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
    
    def add_item(self, product, quantity=1, variant=None):
        with models.atomic():
            item, created = CartItem.objects.select_for_update().get_or_create(
                cart=self, product=product, variant=variant,
                defaults={'quantity': quantity}
            )
            if not created:
                item.quantity = F('quantity') + quantity
                item.save()
                item.refresh_from_db()
            return item

    def remove_item(self, product, variant=None):
        CartItem.objects.filter(cart=self, product=product, variant=variant).delete()


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Merchandise, on_delete=models.CASCADE, null=True, blank=True)
    product_name = models.CharField(max_length=255, null=True, blank=True)
    product_price = models.IntegerField(null=True, blank=True)
    product_thumbnail = models.URLField(null=True, blank=True)
    product_stock = models.IntegerField(null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    selected = models.BooleanField(default=True)
    # variant = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'product')

    def line_total(self):
        price = self.product.price if self.product else (self.product_price or 0)
        return self.quantity * price

    def __str__(self):
        name = self.product.name if self.product else (self.product_name or 'Unknown')
        return f"{name} x{self.quantity}"
