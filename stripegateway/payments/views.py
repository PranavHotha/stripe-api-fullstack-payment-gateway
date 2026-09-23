import stripe
from django.conf import settings
from django.db import connection
# pyrefly: ignore [missing-import]
from rest_framework.decorators import api_view
# pyrefly: ignore [missing-import]
from rest_framework.response import Response
# pyrefly: ignore [missing-import]
from rest_framework import status
# pyrefly: ignore [missing-import]
from .models import Transaction
# pyrefly: ignore [missing-import]
from .serializers import TransactionSerializer, OrderSerializer

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


from django.http import FileResponse, HttpResponse

FRONTEND_DIR = settings.BASE_DIR.parent / 'frontend'


def checkout_view(request):
    """Serve frontend index.html directly from Django"""
    index_file = FRONTEND_DIR / 'index.html'
    if index_file.exists():
        return FileResponse(open(index_file, 'rb'), content_type='text/html')
    return Response({"message": "Welcome to Stripe Payment Gateway Project!"})


def success_view(request):
    """Serve frontend success.html directly from Django"""
    success_file = FRONTEND_DIR / 'success.html'
    if success_file.exists():
        return FileResponse(open(success_file, 'rb'), content_type='text/html')
    return HttpResponse("Payment Successful!")


@api_view(['GET'])
def landing_page(request):
    """Landing page endpoint"""
    return checkout_view(request)


@api_view(['POST'])
def create_payment_intent(request):
    """
    DRF Payment Intent Creation Endpoint:
    - Reads amount and email from request.data
    - Calls Stripe API
    - Saves Transaction in SQLite
    - Returns JSON Response with clientSecret & transactionId
    """
    try:
        amount = request.data.get('amount', 2000)
        email = request.data.get('email', 'customer@example.com')
        
        # Load secret key exclusively from backend settings (.env)
        secret_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
        
        if not secret_key:
            return Response({
                'error': 'Stripe Secret Key is missing. Please configure STRIPE_SECRET_KEY in backend/.env.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        stripe.api_key = secret_key

        # Create Stripe Payment Intent
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency='usd',
            automatic_payment_methods={'enabled': True},
        )

        # Create Transaction in SQLite database
        transaction = Transaction.objects.create(
            stripe_payment_id=intent['id'],
            amount=amount,
            status='pending',
            email=email
        )

        return Response({
            'clientSecret': intent['client_secret'],
            'transactionId': transaction.id,
            'orderId': transaction.id  # Kept for frontend backwards compatibility
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def list_transactions(request):
    """
    DRF Endpoint to fetch all transactions from SQLite database using TransactionSerializer
    """
    transactions = Transaction.objects.all().order_by('-created_at')
    serializer = TransactionSerializer(transactions, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import json

# Backwards compatibility alias
list_orders = list_transactions


@api_view(['POST'])
def reset_transactions(request):
    """
    Dev utility endpoint: Deletes all transactions and resets the ID counter to 1.
    POST /reset-transactions/
    """
    try:
        count, _ = Transaction.objects.all().delete()
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM sqlite_sequence WHERE name = %s",
                ["payments_transaction"]
            )
            if cursor.fetchone()[0]:
                cursor.execute(
                    "UPDATE sqlite_sequence SET seq = 0 WHERE name = %s",
                    ["payments_transaction"]
                )
        return Response({
            'message': f'Cleared {count} transaction(s). ID counter reset to 1.'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def confirm_payment(request):
    """
    Endpoint to verify and confirm payment status with Stripe directly.
    Updates the local Transaction record status to 'succeeded' or 'declined'.
    """
    payment_intent_id = request.data.get('paymentIntentId')
    user_status = request.data.get('status')

    if not payment_intent_id:
        return Response({'error': 'paymentIntentId is required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        secret_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
        if not secret_key:
            return Response({'error': 'STRIPE_SECRET_KEY is not configured.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        stripe.api_key = secret_key
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)

        transaction = Transaction.objects.filter(stripe_payment_id=payment_intent_id).first()
        if not transaction:
            return Response({'error': 'Transaction not found for this payment intent.'}, status=status.HTTP_404_NOT_FOUND)

        if intent.status == 'succeeded':
            transaction.status = 'succeeded'
        elif getattr(intent, 'last_payment_error', None) or user_status == 'declined' or intent.status in ['requires_payment_method', 'canceled']:
            transaction.status = 'declined'

        transaction.save()

        serializer = TransactionSerializer(transaction)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
def stripe_webhook(request):
    """
    Stripe Webhook Listener:
    Handles asynchronous events sent directly from Stripe servers (e.g. payment_intent.succeeded).
    Verifies cryptographic signature if STRIPE_WEBHOOK_SECRET is configured.
    """
    if request.method != 'POST':
        return HttpResponse(status=405)

    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    endpoint_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')

    event = None

    if endpoint_secret:
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError:
            return HttpResponse("Invalid payload", status=400)
        except stripe.error.SignatureVerificationError:
            return HttpResponse("Invalid signature", status=400)
    else:
        # Fallback in local development without webhook secret
        try:
            event = json.loads(payload.decode('utf-8'))
        except Exception:
            return HttpResponse("Invalid JSON", status=400)

    # Extract event data
    event_type = event.get('type') if isinstance(event, dict) else getattr(event, 'type', '')
    data_object = event.get('data', {}).get('object', {}) if isinstance(event, dict) else getattr(getattr(event, 'data', None), 'object', {})

    payment_intent_id = data_object.get('id') if isinstance(data_object, dict) else getattr(data_object, 'id', None)

    if payment_intent_id:
        if event_type == 'payment_intent.succeeded':
            Transaction.objects.filter(stripe_payment_id=payment_intent_id).update(status='succeeded')
        elif event_type in ['payment_intent.payment_failed', 'payment_intent.canceled']:
            Transaction.objects.filter(stripe_payment_id=payment_intent_id).update(status='declined')

    return HttpResponse(status=200)

