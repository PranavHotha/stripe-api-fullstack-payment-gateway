from rest_framework import serializers
from .models import Order

class OrderSerializer(serializers.ModelSerializer):
    amount_in_dollars = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'stripe_payment_id', 'amount', 'amount_in_dollars', 'status', 'email', 'created_at']

    def get_amount_in_dollars(self, obj):
        return f"${obj.amount / 100:.2f}"
