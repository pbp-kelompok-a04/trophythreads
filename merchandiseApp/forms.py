from django.forms import ModelForm
from main.models import Product

class MerchandiseForm(ModelForm):
    class Meta:
        model = Product
        fields = ["name", "price", "category", "stock", "thumbnail", "description", "is_featured"]