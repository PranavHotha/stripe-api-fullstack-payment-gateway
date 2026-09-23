from django.contrib import admin
from django.contrib import messages
from django.db import connection
# pyrefly: ignore [missing-import]
from .models import Transaction


def reset_all_transactions(modeladmin, request, queryset):
    """Admin action: Delete ALL transactions (not just selected) and reset ID to 1."""
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
    modeladmin.message_user(
        request,
        f"✅ Cleared {count} transaction(s). ID counter reset to 1.",
        messages.SUCCESS
    )

reset_all_transactions.short_description = "🗑️ Clear ALL transactions & reset ID to 1"


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'stripe_payment_id', 'amount_in_dollars', 'status', 'email', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('stripe_payment_id', 'email')
    actions = [reset_all_transactions]

    def amount_in_dollars(self, obj):
        return f"${obj.amount / 100:.2f}"
    amount_in_dollars.short_description = "Amount ($)"

