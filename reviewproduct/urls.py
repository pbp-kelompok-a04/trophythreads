
from django.urls import path
from reviewproduct.views import product_reviews, add_review, edit_review, delete_review

app_name = "reviewproduct"

urlpatterns = [
    path('product/<uuid:product_id>/', product_reviews, name='product_reviews'),
    path('product/<uuid:product_id>/add/', add_review, name='add_review'),
    path("review/<uuid:pk>/edit/", edit_review, name="edit_review"), 
    path("review/<uuid:pk>/delete/", delete_review, name="delete_review"),
]