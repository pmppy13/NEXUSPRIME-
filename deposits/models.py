from django.db import models
from django.contrib.auth import get_user_model
import uuid
from django.utils import timezone

User = get_user_model()

class PaymentMethod(models.Model):
    METHOD_TYPES = [
        ('crypto', 'Cryptocurrency'),
        ('cashapp', 'CashApp'),
        ('paypal', 'PayPal'),
        ('bank', 'Bank Transfer'),
    ]
    
    name = models.CharField(max_length=50)
    method_type = models.CharField(max_length=20, choices=METHOD_TYPES)
    is_active = models.BooleanField(default=True)
    
    # Crypto details
    wallet_address = models.CharField(max_length=255, blank=True, null=True)
    network = models.CharField(max_length=50, blank=True, null=True)
    memo_tag = models.CharField(max_length=100, blank=True, null=True)
    
    # Bank details
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    account_name = models.CharField(max_length=100, blank=True, null=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    routing_number = models.CharField(max_length=50, blank=True, null=True)
    swift_code = models.CharField(max_length=20, blank=True, null=True)
    
    # CashApp/PayPal
    cashapp_tag = models.CharField(max_length=50, blank=True, null=True)
    paypal_email = models.EmailField(blank=True, null=True)
    
    # Settings
    minimum_deposit = models.DecimalField(max_digits=12, decimal_places=2, default=10)
    maximum_deposit = models.DecimalField(max_digits=12, decimal_places=2, default=100000)
    instructions = models.TextField(blank=True, null=True)
    sort_order = models.IntegerField(default=0)
    
    def __str__(self):
        return self.name

class Deposit(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    deposit_id = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deposits')
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True)
    amount_usd = models.DecimalField(max_digits=15, decimal_places=2)
    proof_image = models.ImageField(upload_to='proofs/%Y/%m/%d/')
    transaction_hash = models.CharField(max_length=255, blank=True, null=True)
    sender_info = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - ${self.amount_usd} - {self.status}"