# deposits/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import PaymentMethod, Deposit
from accounts.models import Wallet

def send_deposit_approved_email(user, deposit):
    subject = f'Deposit Approved! +${deposit.amount_usd}'
    html_message = render_to_string('emails/deposit_approved.html', {
        'username': user.username,
        'amount': deposit.amount_usd,
        'payment_method': deposit.payment_method.name if deposit.payment_method else 'Bank Transfer',
        'transaction_id': str(deposit.deposit_id)[:8],
        'approved_date': deposit.processed_at.strftime('%B %d, %Y %H:%M'),
        'new_balance': user.wallet.usd_balance,
        'dashboard_url': 'http://localhost:8000/dashboard/',
    })
    send_mail(subject, '', settings.DEFAULT_FROM_EMAIL, [user.email], html_message=html_message, fail_silently=True)

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['name', 'method_type', 'is_active', 'minimum_deposit', 'maximum_deposit', 'sort_order']
    list_filter = ['method_type', 'is_active']
    search_fields = ['name']
    list_editable = ['is_active', 'sort_order']

@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'amount_usd', 'payment_method', 'status', 'proof_preview', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['user__username', 'user__email', 'transaction_hash']
    list_editable = ['status']
    readonly_fields = ['deposit_id', 'created_at']
    
    def proof_preview(self, obj):
        if obj.proof_image:
            return format_html('<img src="{}" width="50" height="50" style="border-radius:5px; object-fit:cover;"/>', obj.proof_image.url)
        return 'No proof'
    proof_preview.short_description = 'Proof'
    
    actions = ['approve_deposits', 'reject_deposits']
    
    def approve_deposits(self, request, queryset):
        count = 0
        for deposit in queryset.filter(status='pending'):
            # Update deposit status
            deposit.status = 'approved'
            deposit.processed_at = timezone.now()
            deposit.save()
            
            # Get or create wallet for user
            wallet, created = Wallet.objects.get_or_create(user=deposit.user)
            
            # Add funds to wallet
            wallet.usd_balance += deposit.amount_usd
            wallet.total_deposited += deposit.amount_usd
            wallet.save()
            
            print(f"Added ${deposit.amount_usd} to {deposit.user.username}'s wallet. New balance: ${wallet.usd_balance}")
            
            # Send email notification
            send_deposit_approved_email(deposit.user, deposit)
            count += 1
            
        self.message_user(request, f'✅ Approved {count} deposit(s). Funds added to user wallets.')
    approve_deposits.short_description = '✅ Approve selected deposits'
    
    def reject_deposits(self, request, queryset):
        count = 0
        for deposit in queryset.filter(status='pending'):
            deposit.status = 'rejected'
            deposit.processed_at = timezone.now()
            deposit.save()
            count += 1
        self.message_user(request, f'❌ Rejected {count} deposit(s).')
    reject_deposits.short_description = '❌ Reject selected deposits'