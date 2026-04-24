from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CookProfile, Dish, DailyMenu, MenuItem, DeliverySlot
from .forms import DishForm, DailyMenuForm, CookProfileForm, DeliverySlotForm
from orders.models import Order
from accounts.decorators import role_required


@role_required(['COOK'])
def dashboard(request):
    try:
        cook = CookProfile.objects.get(user=request.user)
    except CookProfile.DoesNotExist:
        return redirect('cook:onboarding')
    
    # Stats
    total_dishes = Dish.objects.filter(cook=cook).count()
    active_menus = DailyMenu.objects.filter(cook=cook, status='PUBLISHED').count()
    pending_orders = Order.objects.filter(cook=cook, status='PENDING').count()
    confirmed_orders = Order.objects.filter(cook=cook, status='CONFIRMED').count()
    
    # Revenue (Delivered only)
    from django.db.models import Sum
    total_revenue = Order.objects.filter(cook=cook, status='DELIVERED').aggregate(Sum('total'))['total__sum'] or 0
    
    recent_orders = Order.objects.filter(cook=cook).order_by('-placed_at')[:5]
    
    context = {
        'cook': cook,
        'total_dishes': total_dishes,
        'active_menus': active_menus,
        'pending_orders': pending_orders,
        'confirmed_orders': confirmed_orders,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
    }
    return render(request, 'cook/dashboard.html', context)

@role_required(['COOK'])
def dish_list(request):
    try:
        cook = CookProfile.objects.get(user=request.user)
    except CookProfile.DoesNotExist:
        return redirect('cook:onboarding')
    
    dishes = Dish.objects.filter(cook=cook).order_by('-created_at')
    
    context = {
        'cook': cook,
        'dishes': dishes,
    }
    return render(request, 'cook/dish_list.html', context)

@role_required(['COOK'])
def dish_add(request):
    try:
        cook = CookProfile.objects.get(user=request.user)
    except CookProfile.DoesNotExist:
        return redirect('cook:onboarding')
    
    if request.method == 'POST':
        form = DishForm(request.POST, request.FILES)
        if form.is_valid():
            dish = form.save(commit=False)
            dish.cook = cook
            dish.save()
            messages.success(request, 'Dish added successfully.')
            return redirect('cook:dish_list')
    else:
        form = DishForm()
    return render(request, 'cook/dish_form.html', {'form': form, 'cook': cook})

@role_required(['COOK'])
def dish_edit(request, pk):
    try:
        cook = CookProfile.objects.get(user=request.user)
    except CookProfile.DoesNotExist:
        return redirect('cook:onboarding')
    
    dish = get_object_or_404(Dish, pk=pk, cook=cook)
    
    if request.method == 'POST':
        form = DishForm(request.POST, request.FILES, instance=dish)
        if form.is_valid():
            form.save()
            messages.success(request, 'Dish updated successfully.')
            return redirect('cook:dish_list')
    else:
        form = DishForm(instance=dish)
    
    return render(request, 'cook/dish_form.html', {
        'form': form, 
        'cook': cook,
        'dish': dish,
        'is_edit': True
    })

@role_required(['COOK'])
def menu_list(request):
    try:
        cook = CookProfile.objects.get(user=request.user)
    except CookProfile.DoesNotExist:
        return redirect('cook:onboarding')
    
    menus = DailyMenu.objects.filter(cook=cook).order_by('-menu_date', 'meal_type')
    
    context = {
        'cook': cook,
        'menus': menus,
    }
    return render(request, 'cook/menu_list.html', context)

@role_required(['COOK'])
def menu_create(request):
    try:
        cook = CookProfile.objects.get(user=request.user)
    except CookProfile.DoesNotExist:
        return redirect('cook:onboarding')
    
    if request.method == 'POST':
        form = DailyMenuForm(request.POST, cook=cook)
        if form.is_valid():
            # Cook is already on the form via __init__ and used for validation
            menu = form.save(commit=False)
            menu.cook = cook
            menu.save()
            messages.success(request, 'Menu created as Draft. Now add items.')
            return redirect('cook:menu_list')
    else:
        form = DailyMenuForm(cook=cook)
    return render(request, 'cook/menu_form.html', {'form': form, 'cook': cook})

@role_required(['COOK'])
def menu_edit(request, pk):
    try:
        cook = CookProfile.objects.get(user=request.user)
    except CookProfile.DoesNotExist:
        return redirect('cook:onboarding')
    
    menu = get_object_or_404(DailyMenu, pk=pk, cook=cook)
    
    if request.method == 'POST':
        form = DailyMenuForm(request.POST, instance=menu, cook=cook)
        if form.is_valid():
            form.save()
            messages.success(request, 'Menu details updated.')
            return redirect('cook:menu_list')
    else:
        form = DailyMenuForm(instance=menu, cook=cook)
    
    # Manage items
    menu_items = menu.items.all().select_related('dish')
    available_dishes = Dish.objects.filter(cook=cook, is_active=True).exclude(
        id__in=menu_items.values_list('dish_id', flat=True)
    )
    
    context = {
        'cook': cook,
        'menu': menu,
        'form': form,
        'menu_items': menu_items,
        'available_dishes': available_dishes,
    }
    return render(request, 'cook/menu_form.html', context)

@role_required(['COOK'])
def menu_item_add(request, menu_id):
    try:
        cook = CookProfile.objects.get(user=request.user)
    except CookProfile.DoesNotExist:
        return redirect('cook:onboarding')
    
    menu = get_object_or_404(DailyMenu, pk=menu_id, cook=cook)
    
    if request.method == 'POST':
        dish_id = request.POST.get('dish_id')
        qty     = request.POST.get('quantity', 0)
        price   = request.POST.get('price_override')
        
        dish = get_object_or_404(Dish, pk=dish_id, cook=cook)
        
        # Check if dish already exists in menu
        item, created = MenuItem.objects.get_or_create(
            menu=menu,
            dish=dish,
            defaults={
                'quantity_available': qty,
                'price_override': price if price else None
            }
        )
        
        if created:
            messages.success(request, f'{dish.name} added to menu.')
        else:
            # Optionally update quantity if already exists
            item.quantity_available = qty
            if price:
                item.price_override = price
            item.save()
            messages.info(request, f'Updated {dish.name} in menu (was already present).')
    
    return redirect('cook:menu_edit', pk=menu.pk)

@role_required(['COOK'])
def menu_item_remove(request, item_id):
    try:
        cook = CookProfile.objects.get(user=request.user)
    except CookProfile.DoesNotExist:
        return redirect('cook:onboarding')
    
    item = get_object_or_404(MenuItem, pk=item_id, menu__cook=cook)
    menu_id = item.menu_id
    item.delete()
    messages.success(request, 'Item removed from menu.')
    return redirect('cook:menu_edit', pk=menu_id)

@role_required(['COOK'])
def order_list(request):
    try:
        cook = CookProfile.objects.get(user=request.user)
    except CookProfile.DoesNotExist:
        return redirect('cook:onboarding')
    
    orders = Order.objects.filter(cook=cook).order_by('-placed_at')
    
    context = {
        'cook': cook,
        'orders': orders,
    }
    return render(request, 'cook/order_list.html', context)


@role_required(['COOK'])
def order_detail(request, pk):
    try:
        cook = CookProfile.objects.get(user=request.user)
    except CookProfile.DoesNotExist:
        return redirect('cook:onboarding')
    
    order = get_object_or_404(
        Order.objects.select_related('customer', 'slot', 'address')
                     .prefetch_related('items'), 
        pk=pk, 
        cook=cook
    )
    
    context = {
        'cook': cook,
        'order': order,
        'status_choices': Order.Status.choices,
    }
    return render(request, 'cook/order_detail.html', context)


@role_required(['COOK'])
def order_status_update(request, pk):
    try:
        cook = CookProfile.objects.get(user=request.user)
    except CookProfile.DoesNotExist:
        return redirect('cook:onboarding')
    
    order = get_object_or_404(Order, pk=pk, cook=cook)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.Status.choices):
            old_status = order.status
            order.status = new_status
            order.save()
            
            # Restock inventory on failure/cancellation
            if old_status not in ['CANCELLED', 'FAILED'] and new_status in ['CANCELLED', 'FAILED']:
                for item in order.items.all():
                    item.menu_item.quantity_available += item.quantity
                    item.menu_item.save()
                    
            messages.success(request, f'Order status updated to {order.get_status_display()}.')
        else:
            messages.error(request, 'Invalid status.')
            
    return redirect('cook:order_detail', pk=pk)


@role_required(['COOK'])
def onboarding(request):
    # Check if already has profile
    if CookProfile.objects.filter(user=request.user).exists():
        return redirect('cook:dashboard')
        
    if request.method == 'POST':
        form = CookProfileForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, 'Profile completed! Welcome to GharKhana.')
            return redirect('cook:dashboard')
    else:
        form = CookProfileForm(initial={'phone': request.user.phone})
        
    return render(request, 'cook/onboarding.html', {'form': form})

@role_required(['COOK'])
def slot_list(request):
    try:
        cook = CookProfile.objects.get(user=request.user)
    except CookProfile.DoesNotExist:
        return redirect('cook:onboarding')
        
    slots = DeliverySlot.objects.filter(cook=cook)
    form = DeliverySlotForm()
    return render(request, 'cook/slots.html', {'cook': cook, 'slots': slots, 'form': form})

@role_required(['COOK'])
def slot_add(request):
    try:
        cook = CookProfile.objects.get(user=request.user)
    except CookProfile.DoesNotExist:
        return redirect('cook:onboarding')
        
    if request.method == 'POST':
        form = DeliverySlotForm(request.POST)
        if form.is_valid():
            slot = form.save(commit=False)
            slot.cook = cook
            slot.save()
            messages.success(request, 'Delivery slot added.')
    return redirect('cook:slot_list')

@role_required(['COOK'])
def slot_delete(request, pk):
    try:
        cook = CookProfile.objects.get(user=request.user)
    except CookProfile.DoesNotExist:
        return redirect('cook:onboarding')
        
    slot = get_object_or_404(DeliverySlot, pk=pk, cook=cook)
    slot.delete()
    messages.success(request, 'Slot deleted.')
    return redirect('cook:slot_list')

@role_required(['COOK'])
def settings_view(request):
    try:
        cook = CookProfile.objects.get(user=request.user)
    except CookProfile.DoesNotExist:
        return redirect('cook:onboarding')
        
    if request.method == 'POST':
        form = CookProfileForm(request.POST, request.FILES, instance=cook)
        if form.is_valid():
            form.save()
            messages.success(request, 'Settings updated.')
            return redirect('cook:settings')
    else:
        form = CookProfileForm(instance=cook)
        
    context = {
        'cook': cook,
        'form': form,
    }
    return render(request, 'cook/settings.html', context)

