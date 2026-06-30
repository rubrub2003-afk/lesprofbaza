from django.urls import path
from . import views

app_name = "content"

urlpatterns = [
    path("", views.home, name="home"),
    path("calculator/", views.calculator, name="calculator"),
    path("page/<str:slug>/", views.static_page, name="page"),
]
