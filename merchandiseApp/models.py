import uuid
from django.contrib.auth.models import User
from django.db import models

class Merchandise(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    
    CATEGORY_CHOICES = [
        ('jersey', 'Jersey'),
        ('training jersey', 'Training Jersey'),
        ('tops', 'Tops'),
        ('jacket', 'Jacket'),
        ('hoodie', 'Hoodie'),
        ('sweatshirt', 'Sweatshirt'),
        ('vest', 'Vest'),
        ('socks', 'Socks'),
        ('ball', 'Ball'),
        ('bag', 'Bag'),
        ('tumbler', 'Tumbler'),
        ('action figure', 'Action Figure'),
        ('accessories', 'Accessories'),
        ('others', 'Others'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    price = models.IntegerField()
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
    stock = models.IntegerField()
    sold = models.IntegerField(default=0)
    thumbnail = models.URLField(blank=True, null=True)
    description = models.TextField()

    def __str__(self):
        return self.name
    