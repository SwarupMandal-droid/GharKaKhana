from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User
from orders.models import SavedAddress
from cooks.models import CookProfile, Dish

def landing_page(request):
    top_cooks = CookProfile.objects.filter(is_active=True, is_approved=True)[:3]
    top_dishes = Dish.objects.filter(is_active=True)[:6]
    return render(request, 'landing.html', {
        'top_cooks': top_cooks,
        'top_dishes': top_dishes,
    })

def login_view(request):
    if request.user.is_authenticated:
        return redirect_by_role(request.user)

    if request.method == 'POST':
        email    = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        user     = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.name}!')
            return redirect_by_role(user)
        else:
            messages.error(request, 'Invalid email or password.')

    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been signed out.')
    return redirect('landing')


def register_view(request):
    if request.user.is_authenticated:
        return redirect_by_role(request.user)

    if request.method == 'POST':
        name     = request.POST.get('name', '').strip()
        email    = request.POST.get('email', '').strip()
        phone    = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')
        confirm  = request.POST.get('confirm_password', '')
        role     = request.POST.get('role', 'CUSTOMER')

        # Validations
        if not all([name, email, phone, password]):
            messages.error(request, 'All fields are required.')
            return render(request, 'accounts/register.html')

        if password != confirm:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'accounts/register.html')

        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
            return render(request, 'accounts/register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'An account with this email already exists.')
            return render(request, 'accounts/register.html')

        if User.objects.filter(phone=phone).exists():
            messages.error(request, 'An account with this phone number already exists.')
            return render(request, 'accounts/register.html')

        if role not in ['CUSTOMER', 'COOK']:
            role = 'CUSTOMER'

        user = User.objects.create_user(
            email=email,
            phone=phone,
            name=name,
            role=role,
            password=password,
        )
        login(request, user)
        messages.success(request, f'Welcome to GharKhana, {name}!')
        return redirect_by_role(user)

    return render(request, 'accounts/register.html')


@login_required
def profile_view(request):
    addresses = SavedAddress.objects.filter(customer=request.user)
    return render(request, 'accounts/profile.html', {
        'user': request.user,
        'addresses': addresses,
    })

@login_required
def add_address(request):
    if request.method == 'POST':
        label     = request.POST.get('label', 'Home')
        address   = request.POST.get('address', '')
        latitude  = request.POST.get('latitude', '')
        longitude = request.POST.get('longitude', '')
        is_default= request.POST.get('is_default') == 'on'

        if not all([address, latitude, longitude]):
            messages.error(request, 'Please pin your location on the map.')
            return render(request, 'accounts/add_address.html', {
                'label': label,
                'address': address,
                'is_default': is_default,
            })

        SavedAddress.objects.create(
            customer   = request.user,
            label      = label,
            address    = address,
            latitude   = latitude,
            longitude  = longitude,
            is_default = is_default,
        )
        messages.success(request, 'Address saved successfully.')
        return redirect('accounts:profile')

    return render(request, 'accounts/add_address.html')

@login_required
def notifications_view(request):
    notifications = request.user.notifications.order_by('-created_at')[:30]
    # Mark all as read
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'accounts/notifications.html', {
        'notifications': notifications,
    })

def redirect_by_role(user):
    role_redirects = {
        'CUSTOMER': '/cooks/',
        'COOK':     '/cook/dashboard/',
        'DELIVERY': '/delivery/dashboard/',
        'ADMIN':    '/admin-panel/',
    }
    from django.shortcuts import redirect
    return redirect(role_redirects.get(user.role, '/'))