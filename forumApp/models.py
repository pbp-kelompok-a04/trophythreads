from django.db import models
import uuid
from django.contrib.auth.models import User

class ForumPost(models.Model):
    POST_TYPE = [
        ("official", "Official"),
        ("personal", "Personal"),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    image = models.URLField(blank=True, null=True)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    post_type = models.CharField(max_length=10, choices=POST_TYPE, default="personal")
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views = models.IntegerField(default=0)
    
    def __str__(self):
        return self.title
    
    def increment_views(self):
        self.views += 1
        self.save()
    
class Comment(models.Model):
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    image = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)    

    def __str__(self):
        return f"{self.author.username} in {self.post.title}: {self.content[:15]}"
    
