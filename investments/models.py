from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class InvestmentPlan(models.Model):
    name = models.CharField(max_length=100)
    daily_interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    duration_days = models.IntegerField()
    minimum_amount = models.DecimalField(max_digits=12, decimal_places=2)
    maximum_amount = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.name} - {self.daily_interest_rate}%"

class UserInvestment(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='investments')
    plan = models.ForeignKey(InvestmentPlan, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    daily_profit = models.DecimalField(max_digits=15, decimal_places=2)
    total_expected_profit = models.DecimalField(max_digits=15, decimal_places=2)
    total_received_profit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    
    def days_remaining(self):
        delta = self.end_date - timezone.now()
        return max(0, delta.days)
    
    def __str__(self):
        return f"{self.user.username} - {self.plan.name}"