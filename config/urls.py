from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('favicon.ico', RedirectView.as_view(url='/static/images/favicon.ico', permanent=True)),
    path('django-admin/', admin.site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('cooks/',    include('cooks.customer_urls', namespace='customer')),
    path('cook/',     include('cooks.cook_urls',     namespace='cook')),
    path('orders/',   include('orders.urls',         namespace='orders')),
    path('delivery/', include('delivery.urls',       namespace='delivery')),
    path('billing/',  include('billing.urls',        namespace='billing')),
    path('admin-panel/', include('admin_panel.urls', namespace='admin_panel')),
    path('',          RedirectView.as_view(url='/accounts/login/', permanent=False)),
] + static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0]) \
  + static(settings.MEDIA_URL,  document_root=settings.MEDIA_ROOT)