from django.forms import ModelForm
from main.models import ForumPost

class NewsForm(ModelForm):
    class Meta:
        model = ForumPost
        fields = ["title", "content", "category", "thumbnail", "is_featured"]