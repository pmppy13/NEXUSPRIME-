# withdrawals/admin.py
from django.contrib import admin
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import Withdrawal
from accounts.models import Wallet

def send_withdrawal_approved_email(user, withdrawal):
    subject = f'Withdrawal Processed - ${withdrawal.amount_usd}'
    
    # Get recipient info
    if withdrawal.withdrawal_method == 'crypto':
        recipient = withdrawal.wallet_address
    elif withdrawal.withdrawal_method == 'bank':
        recipient = f"{withdrawal.bank_name} - {withdrawal.account_number}"
    elif withdrawal.withdrawal_method == 'paypal':
        recipient = withdrawal.paypal_email
    elif withdrawal.withdrawal_method == 'cashapp':
        recipient = withdrawal.cashapp_tag
    else:
        recipient = 'N/A'
    
    html_message = render_to_string('emails/withdrawal_approved.html', {
        'username': user.username,
        'amount': withdrawal.amount_usd,
        'withdrawal_method': withdrawal.get_withdrawal_method_display(),
        'recipient_address': recipient,
        'processed_date': withdrawal.processed_at.strftime('%B %d, %Y %H:%M'),
        'new_balance': user.wallet.usd_balance,
        'dashboard_url': 'http://localhost:8000/dashboard/',
    })
    send_mail(subject, '', settings.DEFAULT_FROM_EMAIL, [user.email], html_message=html_message, fail_silently=True)

@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'withdrawal_method', 'amount_usd', 'status', 'recipient_info', 'created_at']
    list_filter = ['status', 'withdrawal_method', 'created_at']
    search_fields = ['user__username', 'user__email']
    list_editable = ['status']
    readonly_fields = ['withdrawal_id', 'created_at']
    
    def recipient_info(self, obj):
        if obj.withdrawal_method == 'crypto':
            return obj.wallet_address[:20] + '...' if obj.wallet_address else '-'
        elif obj.withdrawal_method == 'bank':
            return f"{obj.bank_name} - {obj.account_number}"
        elif obj.withdrawal_method == 'paypal':
            return obj.paypal_email
        elif obj.withdrawal_method == 'cashapp':
            return obj.cashapp_tag
        return '-'
    recipient_info.short_description = 'Recipient'
    
    actions = ['approve_withdrawals', 'reject_withdrawals']
    
    def approve_withdrawals(self, request, queryset):
        count = 0
        for withdrawal in queryset.filter(status='pending'):
            withdrawal.status = 'approved'
            withdrawal.processed_at = timezone.now()
            withdrawal.save()
            
            wallet = Wallet.objects.get(user=withdrawal.user)
            wallet.usd_balance -= withdrawal.amount_usd
            wallet.total_withdrawn += withdrawal.amount_usd
            wallet.save()
            
            send_withdrawal_approved_email(withdrawal.user, withdrawal)
            count += 1
            
        self.message_user(request, f'✅ Approved {count} withdrawal(s).')
    approve_withdrawals.short_description = '✅ Approve withdrawals'
    
    def reject_withdrawals(self, request, queryset):
        count = 0
        for withdrawal in queryset.filter(status='pending'):
            withdrawal.status = 'rejected'
            withdrawal.processed_at = timezone.now()
            withdrawal.save()
            count += 1
        self.message_user(request, f'❌ Rejected {count} withdrawal(s).')
    reject_withdrawals.short_description = '❌ Reject withdrawals'