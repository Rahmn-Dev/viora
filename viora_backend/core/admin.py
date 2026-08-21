from django.contrib import admin
from django.contrib.auth.models import User, Group
from .models import WatchHistory, Watchlist, VIPSubscription

# Customize Admin Site Header & Titles
admin.site.site_header = "Viora Cinema Streaming Administration"
admin.site.site_title = "Viora Admin Portal"
admin.site.index_title = "Manage Viora Users, Subscriptions, Invoices & Cinema System"


@admin.register(VIPSubscription)
class VIPSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'invoice_no', 'status', 'amount_paid', 'valid_until', 'created_at')
    list_filter = ('plan', 'status', 'payment_gateway', 'created_at')
    search_fields = ('user__username', 'user__email', 'invoice_no', 'payment_gateway', 'checkout_token')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Account & Access', {
            'fields': ('user', 'plan', 'status', 'is_claimed')
        }),
        ('Billing & Gateway Information', {
            'fields': ('payment_gateway', 'amount_paid', 'valid_until', 'created_at')
        }),
        ('Payment Gateway Invoice Details', {
            'fields': ('reference_id', 'token_id', 'invoice_no', 'payment_link_description')
        }),
        ('Security & Tokens', {
            'fields': ('checkout_token',),
            'classes': ('collapse',)
        })
    )

    readonly_fields = (
        'created_at', 'reference_id', 
        'token_id', 'payment_link_description'
    )

    def reference_id(self, obj):
        if obj.created_at:
            return f"viora-vip-{obj.plan}-{int(obj.created_at.timestamp())}"
        return "-"
    reference_id.short_description = 'Invoice Reference ID (External ID)'
    
    def token_id(self, obj):
        return obj.checkout_token or "-"
    token_id.short_description = 'Token ID'

    def payment_link_description(self, obj):
        return 'Viora VIP Monthly Pass' if obj.plan == 'monthly' else 'Viora VIP 1-Year Pass'
    payment_link_description.short_description = 'Payment Link Description'


@admin.register(WatchHistory)
class WatchHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'tmdb_id', 'media_type', 'progress_percentage', 'updated_at')
    list_filter = ('media_type', 'updated_at')
    search_fields = ('user__username', 'tmdb_id')
    ordering = ('-updated_at',)


@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'tmdb_id', 'title', 'created_at')
    list_filter = ('media_type', 'created_at')
    ordering = ('-created_at',)