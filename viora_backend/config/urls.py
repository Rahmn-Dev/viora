from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect

from core.views import (
    UpdateWatchHistoryView,
    toggle_watchlist,
    get_watchlist,
    api_login,
    api_logout,
    api_me,
    api_save_vip_subscription,
    api_update_profile,
    api_change_password,
    api_register,
    api_create_invoice,
    api_check_invoice_status,
    api_link_invoice,
    api_midtrans_create_transaction,
    api_midtrans_check_status,
    api_midtrans_link_account,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # Xendit Payment Flow (disabled in frontend, kept for legacy)
    path('api/xendit/create-invoice/', api_create_invoice),
    path('api/xendit/check-status/', api_check_invoice_status),
    path('api/xendit/link-account/', api_link_invoice),

    # Midtrans Snap Payment Flow
    path('api/midtrans/create-transaction/', api_midtrans_create_transaction),
    path('api/midtrans/check-status/', api_midtrans_check_status),
    path('api/midtrans/link-account/', api_midtrans_link_account),

    # Auth, Profile & VIP Subscription endpoints (session-based)
    path('api/register/', api_register),
    path('api/login/', api_login),
    path('api/logout/', api_logout),
    path('api/me/', api_me),
    path('api/update-profile/', api_update_profile),
    path('api/change-password/', api_change_password),
    path('api/save-vip-subscription/', api_save_vip_subscription),
   
    # Watch History
    path('api/watch-history/', UpdateWatchHistoryView.as_view(), name='update_watch_history'),

    # Watchlist
    path('api/watchlist/', get_watchlist),
    path('api/watchlist/toggle/', toggle_watchlist),
]