from django.forms import ModelForm
from .models import Merchandise

class MerchandiseForm(ModelForm):
    class Meta:
        model = Merchandise
        fields = ["name", "price", "category", "stock", "thumbnail", "description"]
