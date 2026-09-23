# pyrefly: ignore [missing-import]
from rest_framework import serializers
# pyrefly: ignore [missing-import]
from .models import Transaction
 
class TransactionSerializer(serializers.ModelSerializer):
    amount_in_dollars = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = ['id', 'stripe_payment_id', 'amount', 'amount_in_dollars', 'status', 'email', 'created_at']

    def get_amount_in_dollars(self, obj):
        return f"${obj.amount / 100:.2f}"

# Backwards compatibility alias
OrderSerializer = TransactionSerializer
