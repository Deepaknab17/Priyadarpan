from django.urls import path
from . import views

urlpatterns = [
    path("pay/", views.create_payment, name="create_payment"),
    path("status/", views.payment_status, name="payment_status"),
]