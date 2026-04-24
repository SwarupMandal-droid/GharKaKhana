from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('cook/',                         views.cook_billing,           name='cook_billing'),
    path('cook/bank-details/',            views.save_bank_details,      name='save_bank_details'),
    path('admin/',                        views.admin_billing,          name='admin_billing'),
    path('admin/invoice/<int:pk>/paid/',  views.mark_invoice_paid,      name='mark_invoice_paid'),
    path('admin/generate/',              views.generate_invoice_manual, name='generate_invoice_manual'),
]
