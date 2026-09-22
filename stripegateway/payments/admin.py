from django.contrib import admin
# pyrefly: ignore [missing-import]
from .models import Order

# Register your models here.
admin.site.register(Order)
    
