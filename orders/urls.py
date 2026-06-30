from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("cart/", views.cart, name="cart"),
    path("cart/add/<str:slug>/", views.add_to_cart, name="add"),
    path("cart/remove/<str:slug>/", views.remove_from_cart, name="remove"),
    path("lead/", views.lead, name="lead"),
    path("account/", views.account, name="account"),
    path("reorder/<int:pk>/", views.reorder, name="reorder"),
    path("account/register/", views.register, name="register"),
    path("account/login/", views.login_view, name="login"),
    path("account/logout/", views.logout_view, name="logout"),
]
