from django.contrib import admin
from payments.models import Transaction

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'status', 'esewa_ref_id', 'created_at']
    list_filter = ['status']
    readonly_fields = ['transaction_uuid', 'esewa_ref_id']
