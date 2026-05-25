# withdrawals/models.py
from django.db import models
from django.contrib.auth import get_user_model
import uuid
from django.utils import timezone

User = get_user_model()

class Withdrawal(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]
    
    WITHDRAWAL_METHODS = [
        ('crypto', 'Cryptocurrency'),
        ('bank', 'Bank Transfer'),
        ('paypal', 'PayPal'),
        ('cashapp', 'CashApp'),
    ]
    
    CRYPTO_CHOICES = [
        ('BTC', 'Bitcoin (BTC)'),
        ('ETH', 'Ethereum (ETH)'),
        ('USDT', 'USDT (TRC20)'),
        ('USDC', 'USDC (ERC20)'),
        ('SOL', 'Solana (SOL)'),
        ('BNB', 'Binance Coin (BNB)'),
        ('XRP', 'Ripple (XRP)'),
        ('DOGE', 'Dogecoin (DOGE)'),
        ('ADA', 'Cardano (ADA)'),
        ('LTC', 'Litecoin (LTC)'),
    ]
    
    # Basic info
    withdrawal_id = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='withdrawals')
    
    # Withdrawal method
    withdrawal_method = models.CharField(max_length=20, choices=WITHDRAWAL_METHODS, default='crypto')
    
    # Amount
    amount_usd = models.DecimalField(max_digits=15, decimal_places=2)
    
    # For CRYPTO withdrawals
    crypto_currency = models.CharField(max_length=10, choices=CRYPTO_CHOICES, blank=True, null=True)
    crypto_amount = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    wallet_address = models.CharField(max_length=255, blank=True, null=True, help_text="Your crypto wallet address")
    network = models.CharField(max_length=50, blank=True, null=True, help_text="Network (ERC20, TRC20, BEP20, etc.)")
    memo_tag = models.CharField(max_length=100, blank=True, null=True, help_text="Memo/Destination tag (if required)")
    
    # For BANK withdrawals
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    account_name = models.CharField(max_length=100, blank=True, null=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    routing_number = models.CharField(max_length=50, blank=True, null=True, help_text="Routing/ABA number (US banks)")
    swift_code = models.CharField(max_length=20, blank=True, null=True, help_text="SWIFT/BIC code for international transfers")
    iban = models.CharField(max_length=50, blank=True, null=True, help_text="IBAN for international transfers")
    
    # For PayPal withdrawals
    paypal_email = models.EmailField(blank=True, null=True, help_text="Your PayPal email address")
    
    # For CashApp withdrawals
    cashapp_tag = models.CharField(max_length=50, blank=True, null=True, help_text="Your $Cashtag")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Withdrawal'
        verbose_name_plural = 'Withdrawals'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_withdrawal_method_display()} - ${self.amount_usd} - {self.get_status_display()}"
    
    def get_recipient_display(self):
        """Return a readable recipient string for display"""
        if self.withdrawal_method == 'crypto':
            return f"{self.crypto_currency}: {self.wallet_address[:20]}..." if self.wallet_address else "No address"
        elif self.withdrawal_method == 'bank':
            return f"{self.bank_name} - {self.account_number}" if self.bank_name else "No bank info"
        elif self.withdrawal_method == 'paypal':
            return self.paypal_email or "No email"
        elif self.withdrawal_method == 'cashapp':
            return self.cashapp_tag or "No tag"
        return "N/A"
    
    def get_recipient_full(self):
        """Return full recipient details"""
        if self.withdrawal_method == 'crypto':
            return {
                'currency': self.crypto_currency,
                'address': self.wallet_address,
                'network': self.network,
                'memo': self.memo_tag,
            }
        elif self.withdrawal_method == 'bank':
            return {
                'bank': self.bank_name,
                'account_name': self.account_name,
                'account_number': self.account_number,
                'routing': self.routing_number,
                'swift': self.swift_code,
                'iban': self.iban,
            }
        elif self.withdrawal_method == 'paypal':
            return {'email': self.paypal_email}
        elif self.withdrawal_method == 'cashapp':
            return {'tag': self.cashapp_tag}
        return {}
    
    def is_pending(self):
        return self.status == 'pending'
    
    def is_approved(self):
        return self.status == 'approved'
    
    def is_rejected(self):
        return self.status == 'rejected'
    
    def can_process(self):
        return self.status == 'pending'