from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import random
import string

class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    
    def __str__(self):
        return self.username

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    usd_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    btc_balance = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    eth_balance = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    usdt_balance = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    total_profit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_deposited = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_withdrawn = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    def __str__(self):
        return f"{self.user.username}'s Wallet"

class PasswordResetCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def is_expired(self):
        expiry_time = self.created_at + timezone.timedelta(minutes=10)
        return timezone.now() > expiry_time
    
    @staticmethod
    def generate_code():
        return ''.join(random.choices(string.digits, k=6))