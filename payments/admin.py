from django.contrib import admin
from payments.models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'provider', 'transaction_id', 'amount', 'status', 'created_at']
    list_filter = ['provider', 'status', 'created_at']
    search_fields = ['transaction_id', 'order__id', 'order__user__email']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'completed_at']
