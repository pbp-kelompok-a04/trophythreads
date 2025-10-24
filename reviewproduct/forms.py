from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "body"]
        widgets = {
            "body": forms.Textarea(attrs={
            "rows": 4, "placeholder": "Share your thoughts"
            }),
        }
