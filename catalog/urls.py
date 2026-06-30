from django.urls import path
from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.catalog_index, name="index"),
    path("search/", views.search, name="search"),
    path("compare/", views.compare_view, name="compare"),
    path("favorites/", views.favorites_view, name="favorites"),
    path("category/<str:slug>/", views.category_view, name="category"),
    path("product/<str:slug>/", views.product_view, name="product"),
    path("product/<str:slug>/review/", views.add_review, name="add_review"),
]
