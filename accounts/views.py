from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from .models import User, Wallet, PasswordResetCode

def home(request):
    return render(request, 'broker/home.html')

def about(request):
    return render(request, 'broker/about.html')

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match!')
            return render(request, 'broker/signup.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken!')
            return render(request, 'broker/signup.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered!')
            return render(request, 'broker/signup.html')
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        Wallet.objects.create(user=user)
        
        login(request, user)
        messages.success(request, f'Welcome {username}!')
        return redirect('dashboard')
    
    return render(request, 'broker/signup.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is None and '@' in username:
            try:
                user_obj = User.objects.get(email=username)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass
        
        if user:
            login(request, user)
            messages.success(request, f'Welcome back {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username/email or password.')
    
    return render(request, 'broker/login.html')

def logout_view(request):
    logout(request)
    messages.info(request, 'Logged out successfully')
    return redirect('home')

@login_required
def dashboard(request):
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    return render(request, 'broker/dashboard.html', {'wallet': wallet})

def forgot_password_view(request):
    if request.method == "POST":
        email = request.POST.get('email', '').lower().strip()
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "No account found with that email.")
            return render(request, "broker/password_reset.html")
        
        code = PasswordResetCode.generate_code()
        PasswordResetCode.objects.create(user=user, code=code)
        
        html_message = render_to_string("emails/password_reset_code.html", {
            "name": user.first_name or user.username,
            "code": code,
            "minutes": 10,
            "year": timezone.now().year,
        })
        
        msg = EmailMultiAlternatives(
            subject="Password Reset Code",
            body=f"Your code is: {code}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send()
        
        messages.success(request, "We sent a reset code to your email.")
        return redirect("password_reset_done")
    
    return render(request, "broker/password_reset.html")

def password_reset_done(request):
    return render(request, 'broker/password_reset_done.html')

def password_reset_confirm(request, uidb64=None, token=None):
    return render(request, 'broker/password_reset_confirm.html')

def password_reset_complete(request):
    return render(request, 'broker/password_reset_complete.html')