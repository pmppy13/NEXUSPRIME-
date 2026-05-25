# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Wallet, PasswordResetCode

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'is_staff', 'is_active', 'date_joined']
    search_fields = ['username', 'email']
    list_filter = ['is_staff', 'is_active']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('phone',)}),
    )

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'usd_balance', 'total_profit', 'total_deposited', 'total_withdrawn']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['total_profit', 'total_deposited', 'total_withdrawn']
    
    actions = ['add_profit_to_users']
    
    def add_profit_to_users(self, request, queryset):
        amount = 100
        count = 0
        for wallet in queryset:
            wallet.usd_balance += amount
            wallet.total_profit += amount
            wallet.save()
            count += 1
        self.message_user(request, f'💰 Added ${amount} profit to {count} user(s)')
    add_profit_to_users.short_description = '💰 Add $100 profit to selected users'

@admin.register(PasswordResetCode)
class PasswordResetCodeAdmin(admin.ModelAdmin):
    list_display = ['user', 'code', 'is_used', 'created_at']
    list_filter = ['is_used', 'created_at']
    search_fields = ['user__username']