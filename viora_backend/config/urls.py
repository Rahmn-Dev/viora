from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
# Pastikan import view yang baru kita buat (sesuaikan nama 'my_app' dengan nama aplikasimu)
from core.views import UpdateWatchHistoryView, toggle_watchlist, get_watchlist

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Endpoint Authentication (JWT)
    path('api/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Endpoint Watch History
     path('api/watchlist/toggle/', toggle_watchlist),
    path('api/watch-history/', UpdateWatchHistoryView.as_view(), name='update_watch_history'),
    path('api/watchlist/', get_watchlist),
]