import stripe
from django.conf import settings
# pyrefly: ignore [missing-import]
from rest_framework.decorators import api_view
# pyrefly: ignore [missing-import]
from rest_framework.response import Response
# pyrefly: ignore [missing-import]
from rest_framework import status
# pyrefly: ignore [missing-import]
from .models import Order
# pyrefly: ignore [missing-import]
from .serializers import OrderSerializer

# Configure Stripe with Secret Key if present
if getattr(settings, 'STRIPE_SECRET_KEY', None):
    stripe.api_key = settings.STRIPE_SECRET_KEY


@api_view(['GET'])
def get_config(request):
    """
    Return publishable key and whether secret key exists in backend settings/env.
    """
    pub_key = getattr(settings, 'STRIPE_PUBLISHABLE_KEY', '')
    has_secret = bool(getattr(settings, 'STRIPE_SECRET_KEY', ''))
    return Response({
        'publishableKey': pub_key,
        'hasSecretKey': has_secret
    })


@api_view(['GET'])
def health_check(request):
    """Health check endpoint"""
    return Response({"message": "Payment service is running!"})


@api_view(['GET'])
def landing_page(request):
    """Landing page endpoint"""
    return Response({"message": "Welcome to Stripe Payment Gateway Project!"})


@api_view(['POST'])
def create_payment_intent(request):
    """
    DRF Payment Intent Creation Endpoint:
    - Reads amount, email, and optional custom secretKey from request.data
    - Calls Stripe API
    - Saves Order in SQLite
    - Returns JSON Response with clientSecret & orderId
    """
    try:
        amount = request.data.get('amount', 2000)
        email = request.data.get('email', 'customer@example.com')
        
        # Use custom secret key from request if provided, otherwise use backend setting
        secret_key = request.data.get('secretKey') or getattr(settings, 'STRIPE_SECRET_KEY', '')
        
        if not secret_key:
            return Response({
                'error': 'Stripe Secret Key is missing! Please enter your Stripe Secret Key in the key configuration field on the page or set STRIPE_SECRET_KEY in backend/.env.'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        stripe.api_key = secret_key

        # Create Stripe Payment Intent
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency='usd',
            automatic_payment_methods={'enabled': True},
        )

        # Create Order in SQLite database
        order = Order.objects.create(
            stripe_payment_id=intent['id'],
            amount=amount,
            status='pending',
            email=email
        )

        return Response({
            'clientSecret': intent['client_secret'],
            'orderId': order.id
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def list_orders(request):
    """
    DRF Endpoint to fetch all orders from SQLite database using OrderSerializer
    """
    orders = Order.objects.all().order_by('-created_at')
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
