# deposits/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from decimal import Decimal
from .models import PaymentMethod, Deposit
from accounts.models import Wallet

# Email function for deposit submitted
def send_deposit_submitted_email(user, deposit):
    subject = f'Deposit Request Received - ${deposit.amount_usd}'
    html_message = render_to_string('emails/deposit_submitted.html', {
        'username': user.username,
        'amount': deposit.amount_usd,
        'payment_method': deposit.payment_method.name if deposit.payment_method else 'Bank Transfer',
        'transaction_id': str(deposit.deposit_id)[:8],  # ← FIX: Convert UUID to string
        'submitted_date': deposit.created_at.strftime('%B %d, %Y %H:%M'),
        'dashboard_url': 'http://localhost:8000/dashboard/',
    })
    send_mail(subject, '', settings.DEFAULT_FROM_EMAIL, [user.email], html_message=html_message, fail_silently=True)

@login_required
def deposit_view(request):
    payment_methods = PaymentMethod.objects.filter(is_active=True)
    
    if request.method == 'POST':
        payment_method_id = request.POST.get('payment_method')
        amount = request.POST.get('amount_usd')
        proof_image = request.FILES.get('proof_image')
        transaction_hash = request.POST.get('transaction_hash', '')
        sender_info = request.POST.get('sender_info', '')
        
        if not payment_method_id or not amount or not proof_image:
            messages.error(request, 'Please fill all required fields')
            return render(request, 'broker/deposit.html', {'payment_methods': payment_methods})
        
        payment_method = get_object_or_404(PaymentMethod, id=payment_method_id)
        amount_decimal = Decimal(amount)
        
        if amount_decimal < payment_method.minimum_deposit:
            messages.error(request, f'Minimum deposit is ${payment_method.minimum_deposit}')
            return render(request, 'broker/deposit.html', {'payment_methods': payment_methods})
        
        if amount_decimal > payment_method.maximum_deposit:
            messages.error(request, f'Maximum deposit is ${payment_method.maximum_deposit}')
            return render(request, 'broker/deposit.html', {'payment_methods': payment_methods})
        
        deposit = Deposit.objects.create(
            user=request.user,
            payment_method=payment_method,
            amount_usd=amount_decimal,
            proof_image=proof_image,
            transaction_hash=transaction_hash,
            sender_info=sender_info,
            status='pending'
        )
        
        # SEND EMAIL - Deposit Submitted
        send_deposit_submitted_email(request.user, deposit)
        
        messages.success(request, '✅ Deposit request submitted! Admin will review.')
        return redirect('dashboard')
    
    return render(request, 'broker/deposit.html', {'payment_methods': payment_methods})