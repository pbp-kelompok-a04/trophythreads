from django.urls import path
from reviewproduct.views import product_reviews, review_page, add_review,edit_review,delete_review


app_name = "reviewproduct"

urlpatterns = [
    # HTML PAGE
    path('product/<uuid:product_id>/', product_reviews, name='product_reviews'),

    # JSON API
    path('api/product/<uuid:product_id>/', review_page, name='product_reviews_json'),
    path('api/product/<uuid:product_id>/add/', add_review, name='add_review'),
    path("api/review/<uuid:pk>/edit/", edit_review, name="edit_review"),
    path("api/review/<uuid:pk>/delete/", delete_review, name="delete_review"),
]
