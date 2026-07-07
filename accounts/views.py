from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Count
from .models import User
from orders.models import SavedAddress
from cooks.models import CookProfile, Dish
from orders.models import Order


def landing_page(request):
    if request.user.is_authenticated:
        return redirect_by_role(request.user)

    top_cooks = (
        CookProfile.objects.filter(is_active=True, is_approved=True)
        .annotate(
            avg_rating=Avg('reviews__rating'),
            review_count=Count('reviews'),
        )
        .order_by('-avg_rating', '-review_count', 'kitchen_name')[:3]
    )
    top_dishes = (
        Dish.objects.filter(is_active=True, cook__is_active=True, cook__is_approved=True)
        .annotate(order_count=Count('menu_items__order_items'))
        .order_by('-order_count', 'name')[:6]
    )
    avg_rating = (
        CookProfile.objects.filter(is_active=True, is_approved=True)
        .aggregate(avg=Avg('reviews__rating'))['avg']
    )
    landing_metrics = {
        'verified_kitchens': CookProfile.objects.filter(
            is_active=True,
            is_approved=True,
        ).count(),
        'meals_delivered': Order.objects.filter(status=Order.Status.DELIVERED).count(),
        'avg_rating': round(avg_rating, 1) if avg_rating else None,
        'active_dishes': Dish.objects.filter(
            is_active=True,
            cook__is_active=True,
            cook__is_approved=True,
        ).count(),
    }

    return render(request, 'landing.html', {
        'top_cooks': top_cooks,
        'top_dishes': top_dishes,
        'landing_metrics': landing_metrics,
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
    return redirect('accounts:login')


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
def edit_address(request, pk):
    address = get_object_or_404(SavedAddress, pk=pk, customer=request.user)
    if request.method == 'POST':
        address.label      = request.POST.get('label', address.label)
        address.address    = request.POST.get('address', address.address)
        address.latitude   = request.POST.get('latitude', address.latitude)
        address.longitude  = request.POST.get('longitude', address.longitude)
        address.is_default = request.POST.get('is_default') == 'on'
        
        address.save()
        messages.success(request, 'Address updated successfully.')
        return redirect('accounts:profile')

    return render(request, 'accounts/add_address.html', {'address': address, 'is_edit': True})

@login_required
def delete_address(request, pk):
    address = get_object_or_404(SavedAddress, pk=pk, customer=request.user)
    if request.method == 'POST':
        address.delete()
        messages.success(request, 'Address deleted successfully.')
    return redirect('accounts:profile')

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
        'COOK':     '/cook/setup/',
        'DELIVERY': '/delivery/dashboard/',
        'ADMIN':    '/admin-panel/',
    }
    from django.shortcuts import redirect
    return redirect(role_redirects.get(user.role, '/'))
