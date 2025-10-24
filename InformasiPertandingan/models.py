import uuid
from django.contrib.auth.models import User
from django.db import models

class Country(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) 
    name = models.CharField(max_length=100) 
    flag = models.URLField()
    
    def __str__(self): 
        return self.name
    
class Informasi(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) 
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=255) 
    date = models.DateField() 
    city = models.CharField(max_length=100) 
    country = models.CharField(max_length=100)
    home_team = models.ForeignKey(Country, related_name='home_matches', on_delete=models.CASCADE) 
    away_team = models.ForeignKey(Country, related_name='away_matches', on_delete=models.CASCADE) 
    score_home_team = models.PositiveIntegerField(default=0) 
    score_away_team = models.PositiveIntegerField(default=0) 
    views = models.PositiveIntegerField(default=0) 
    
    def __str__(self): 
        return self.title 
    
    @property
    def is_info_hot(self):
        return self.views > 20

    def increment_views(self):
        self.views += 1
        self.save()     