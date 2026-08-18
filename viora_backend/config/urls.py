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
    
)

urlpatterns = [
    path("", lambda request: redirect("/admin/")),
    path('admin/', admin.site.urls),

    # Auth endpoints (session-based)
    path('api/login/', api_login),
    path('api/logout/', api_logout),
    path('api/me/', api_me),
   
    # Watch History
    path('api/watch-history/', UpdateWatchHistoryView.as_view(), name='update_watch_history'),

    # Watchlist
    path('api/watchlist/', get_watchlist),
    path('api/watchlist/toggle/', toggle_watchlist),
]