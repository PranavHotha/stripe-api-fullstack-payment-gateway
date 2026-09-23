
from django.urls import path
from django.views.static import serve
from django.conf import settings
# pyrefly: ignore [missing-import]
from . import views

FRONTEND_DIR = settings.BASE_DIR.parent / 'frontend'

urlpatterns = [
    path('', views.checkout_view, name="checkout"),
    path('success.html', views.success_view, name="success"),
    path('style.css', serve, {'document_root': FRONTEND_DIR, 'path': 'style.css'}),
    path('script.js', serve, {'document_root': FRONTEND_DIR, 'path': 'script.js'}),
    path('config/', views.get_config, name='get_config'),
    path('health/', views.health_check, name='health_check'),
    path('create-payment-intent/', views.create_payment_intent, name='create_payment_intent'),
    path('reset-transactions/', views.reset_transactions, name='reset_transactions'),
    path('confirm-payment/', views.confirm_payment, name='confirm_payment'),
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('transactions/', views.list_transactions, name='list_transactions'),
    path('orders/', views.list_orders, name='list_orders'),  # Backwards compatibility
]
