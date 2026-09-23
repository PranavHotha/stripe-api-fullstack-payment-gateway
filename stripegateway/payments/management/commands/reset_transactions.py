from django.core.management.base import BaseCommand
from django.db import connection
from payments.models import Transaction


class Command(BaseCommand):
    help = "Clears all transactions and resets the auto-increment ID counter back to 1."

    def handle(self, *args, **options):
        count, _ = Transaction.objects.all().delete()
        with connection.cursor() as cursor:
            # Check if a sequence entry exists for this table
            cursor.execute(
                "SELECT COUNT(*) FROM sqlite_sequence WHERE name = %s",
                ["payments_transaction"]
            )
            exists = cursor.fetchone()[0]

            if exists:
                # Set sequence to 0 so next insert gets ID 1
                cursor.execute(
                    "UPDATE sqlite_sequence SET seq = 0 WHERE name = %s",
                    ["payments_transaction"]
                )
            # If no row exists yet (table never had any rows), SQLite will
            # auto-create it starting at 1 on the next insert — nothing to do.

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully deleted {count} transaction(s) and reset ID counter to 1."
            )
        )

