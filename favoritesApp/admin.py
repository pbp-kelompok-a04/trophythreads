from django.contrib import admin
from .models import Favorite

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'merchandise', 'created_at')
    search_fields = ('user__username', 'merchandise__name')
    list_filter = ('created_at',)
