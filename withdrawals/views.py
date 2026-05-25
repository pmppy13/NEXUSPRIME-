# withdrawals/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from decimal import Decimal
from .models import Withdrawal
from accounts.models import Wallet

def send_withdrawal_submitted_email(user, withdrawal):
    subject = f'Withdrawal Request Received - ${withdrawal.amount_usd}'
    
    # Get method display name
    method_display = dict(Withdrawal.WITHDRAWAL_METHODS).get(withdrawal.withdrawal_method, withdrawal.withdrawal_method)
    
    html_message = render_to_string('emails/withdrawal_submitted.html', {
        'username': user.username,
        'amount': withdrawal.amount_usd,
        'withdrawal_method': method_display,
        'crypto_currency': withdrawal.crypto_currency,
        'recipient_address': withdrawal.wallet_address or withdrawal.paypal_email or withdrawal.cashapp_tag or withdrawal.account_number,
        'submitted_date': withdrawal.created_at.strftime('%B %d, %Y %H:%M'),
        'dashboard_url': 'http://localhost:8000/dashboard/',
    })
    send_mail(subject, '', settings.DEFAULT_FROM_EMAIL, [user.email], html_message=html_message, fail_silently=True)

@login_required
def withdrawal_view(request):
    wallet = Wallet.objects.get(user=request.user)
    withdrawals = Withdrawal.objects.filter(user=request.user)[:10]
    
    if request.method == 'POST':
        withdrawal_method = request.POST.get('withdrawal_method')
        amount = request.POST.get('amount')
        
        if not withdrawal_method or not amount:
            messages.error(request, 'Please fill all required fields')
            return render(request, 'broker/withdrawal.html', {'wallet': wallet, 'withdrawals': withdrawals})
        
        amount_decimal = Decimal(amount)
        
        if amount_decimal < 10:
            messages.error(request, 'Minimum withdrawal is $10')
            return render(request, 'broker/withdrawal.html', {'wallet': wallet, 'withdrawals': withdrawals})
        
        if wallet.usd_balance < amount_decimal:
            messages.error(request, f'Insufficient balance. You have ${wallet.usd_balance}')
            return render(request, 'broker/withdrawal.html', {'wallet': wallet, 'withdrawals': withdrawals})
        
        # Create withdrawal based on method
        withdrawal_data = {
            'user': request.user,
            'withdrawal_method': withdrawal_method,
            'amount_usd': amount_decimal,
            'status': 'pending'
        }
        
        # Add method-specific fields
        if withdrawal_method == 'crypto':
            crypto_currency = request.POST.get('crypto_currency')
            wallet_address = request.POST.get('wallet_address')
            
            if not crypto_currency or not wallet_address:
                messages.error(request, 'Please select cryptocurrency and enter wallet address')
                return render(request, 'broker/withdrawal.html', {'wallet': wallet, 'withdrawals': withdrawals})
            
            # Calculate crypto amount (simplified rates)
            rates = {'BTC': 60000, 'ETH': 3000, 'USDT': 1, 'USDC': 1, 'SOL': 150, 'BNB': 580, 'XRP': 0.6, 'DOGE': 0.08}
            crypto_amount = amount_decimal / rates.get(crypto_currency, 1)
            
            withdrawal_data['crypto_currency'] = crypto_currency
            withdrawal_data['crypto_amount'] = crypto_amount
            withdrawal_data['wallet_address'] = wallet_address
            
        elif withdrawal_method == 'bank':
            bank_name = request.POST.get('bank_name')
            account_name = request.POST.get('account_name')
            account_number = request.POST.get('account_number')
            routing_number = request.POST.get('routing_number', '')
            swift_code = request.POST.get('swift_code', '')
            
            if not all([bank_name, account_name, account_number]):
                messages.error(request, 'Please fill all bank details')
                return render(request, 'broker/withdrawal.html', {'wallet': wallet, 'withdrawals': withdrawals})
            
            withdrawal_data['bank_name'] = bank_name
            withdrawal_data['account_name'] = account_name
            withdrawal_data['account_number'] = account_number
            withdrawal_data['routing_number'] = routing_number
            withdrawal_data['swift_code'] = swift_code
            
        elif withdrawal_method == 'paypal':
            paypal_email = request.POST.get('paypal_email')
            
            if not paypal_email:
                messages.error(request, 'Please enter PayPal email')
                return render(request, 'broker/withdrawal.html', {'wallet': wallet, 'withdrawals': withdrawals})
            
            withdrawal_data['paypal_email'] = paypal_email
            
        elif withdrawal_method == 'cashapp':
            cashapp_tag = request.POST.get('cashapp_tag')
            
            if not cashapp_tag:
                messages.error(request, 'Please enter CashApp tag')
                return render(request, 'broker/withdrawal.html', {'wallet': wallet, 'withdrawals': withdrawals})
            
            withdrawal_data['cashapp_tag'] = cashapp_tag
        
        withdrawal = Withdrawal.objects.create(**withdrawal_data)
        
        # Send email
        send_withdrawal_submitted_email(request.user, withdrawal)
        
        messages.success(request, '✅ Withdrawal request submitted! Admin will review.')
        return redirect('withdrawal')
    
    return render(request, 'broker/withdrawal.html', {
        'wallet': wallet,
        'withdrawals': withdrawals
    })