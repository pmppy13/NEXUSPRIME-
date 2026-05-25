# investments/admin.py
from django.contrib import admin
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import InvestmentPlan, UserInvestment

def send_daily_profit_email(user, amount, plan_name, total_received, expected_total, new_balance):
    subject = f'Daily Profit Added! +${amount}'
    html_message = render_to_string('emails/profit_added.html', {
        'username': user.username,
        'amount': amount,
        'plan_name': plan_name,
        'total_received': total_received,
        'expected_total': expected_total,
        'new_balance': new_balance,
        'dashboard_url': 'http://localhost:8000/dashboard/',
    })
    send_mail(subject, '', settings.DEFAULT_FROM_EMAIL, [user.email], html_message=html_message, fail_silently=True)

@admin.register(InvestmentPlan)
class InvestmentPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'daily_interest_rate', 'duration_days', 'minimum_amount', 'maximum_amount', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']
    list_editable = ['is_active']

@admin.register(UserInvestment)
class UserInvestmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'amount', 'daily_profit', 'total_received_profit', 'status', 'start_date']
    list_filter = ['status', 'plan']
    search_fields = ['user__username']
    readonly_fields = ['start_date']
    
    actions = ['add_daily_profit']
    
    def add_daily_profit(self, request, queryset):
        from django.utils import timezone
        count = 0
        for investment in queryset.filter(status='active'):
            investment.total_received_profit += investment.daily_profit
            investment.save()
            
            wallet = investment.user.wallet
            wallet.usd_balance += investment.daily_profit
            wallet.total_profit += investment.daily_profit
            wallet.save()
            
            send_daily_profit_email(
                investment.user, 
                float(investment.daily_profit),
                investment.plan.name,
                float(investment.total_received_profit),
                float(investment.total_expected_profit),
                float(wallet.usd_balance)
            )
            count += 1
            
        self.message_user(request, f'💰 Added daily profit to {count} investment(s) and sent email notifications')
    add_daily_profit.short_description = '💰 Add daily profit to selected investments'