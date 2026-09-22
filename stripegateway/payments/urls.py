
from django.urls import path
# pyrefly: ignore [missing-import]
from . import views

urlpatterns = [
    path('', views.landing_page, name="landing_page"),
    path('config/', views.get_config, name='get_config'),
    path('health/', views.health_check, name='health_check'),
    path('create-payment-intent/', views.create_payment_intent, name='create_payment_intent'),
    path('orders/', views.list_orders, name='list_orders'),
]
