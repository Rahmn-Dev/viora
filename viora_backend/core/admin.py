from django.contrib import admin
from .models import WatchHistory, Watchlist


@admin.register(WatchHistory)
class WatchHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'tmdb_id', 'media_type', 'progress_percentage', 'updated_at')
    list_filter = ('media_type', 'updated_at')
    search_fields = ('user__username', 'tmdb_id')
    ordering = ('-updated_at',)

    # 🔥 biar gampang cek existing
    def has_change_permission(self, request, obj=None):
        return True


@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'tmdb_id', 'title', 'created_at')
    list_filter = ('media_type', 'created_at')
    ordering = ('-created_at',)