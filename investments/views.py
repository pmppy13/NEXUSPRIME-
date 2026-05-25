# investments/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from .models import InvestmentPlan, UserInvestment
from accounts.models import Wallet

# Email function for investment confirmed
def send_investment_confirmed_email(user, investment):
    subject = f'Investment Confirmed - ${investment.amount} in {investment.plan.name}'
    html_message = render_to_string('emails/investment_confirmed.html', {
        'username': user.username,
        'amount': investment.amount,
        'plan_name': investment.plan.name,
        'daily_rate': investment.plan.daily_interest_rate,
        'duration_days': investment.plan.duration_days,
        'daily_profit': investment.daily_profit,
        'expected_return': float(investment.amount) + float(investment.total_expected_profit),
        'start_date': investment.start_date.strftime('%B %d, %Y'),
        'end_date': investment.end_date.strftime('%B %d, %Y'),
        'dashboard_url': 'http://localhost:8000/dashboard/',
    })
    send_mail(subject, '', settings.DEFAULT_FROM_EMAIL, [user.email], html_message=html_message, fail_silently=True)

@login_required
def investments_view(request):
    investment_plans = InvestmentPlan.objects.filter(is_active=True)
    user_investments = UserInvestment.objects.filter(user=request.user)
    wallet = Wallet.objects.get(user=request.user)
    
    if request.method == 'POST':
        plan_id = request.POST.get('plan_id')
        amount = Decimal(request.POST.get('amount'))
        plan = get_object_or_404(InvestmentPlan, id=plan_id)
        
        if amount < plan.minimum_amount or amount > plan.maximum_amount:
            messages.error(request, 'Invalid amount for this plan')
            return redirect('investments')
        
        if wallet.usd_balance < amount:
            messages.error(request, 'Insufficient balance')
            return redirect('investments')
        
        daily_profit = amount * (plan.daily_interest_rate / 100)
        total_profit = daily_profit * plan.duration_days
        end_date = timezone.now() + timezone.timedelta(days=plan.duration_days)
        
        wallet.usd_balance -= amount
        wallet.save()
        
        investment = UserInvestment.objects.create(
            user=request.user,
            plan=plan,
            amount=amount,
            daily_profit=daily_profit,
            total_expected_profit=total_profit,
            end_date=end_date
        )
        
        # SEND EMAIL - Investment Confirmed
        send_investment_confirmed_email(request.user, investment)
        
        messages.success(request, f'✅ Successfully invested ${amount} in {plan.name}!')
        return redirect('investments')
    
    return render(request, 'broker/investments.html', {
        'investment_plans': investment_plans,
        'user_investments': user_investments,
        'wallet': wallet
    })