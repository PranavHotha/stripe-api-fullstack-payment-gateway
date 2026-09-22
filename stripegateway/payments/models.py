from django.db import models

# Create your models here.

class Order(models.Model):
    stripe_payment_id = models.CharField(max_length=255, unique=True, blank=True, null=True)
    amount = models.IntegerField(help_text="Amount in cents")
    status = models.CharField(max_length=50, default='pending') #pending, succeeded, failed 
    email = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"Order {self.id} | {self.status}"

        
