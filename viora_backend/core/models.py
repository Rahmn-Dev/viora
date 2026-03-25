from django.db import models
from django.contrib.auth.models import User

class WatchHistory(models.fields):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watch_history')
    tmdb_id = models.IntegerField()
    media_type = models.CharField(max_length=10, choices=[('movie', 'Movie'), ('tv', 'TV Show')])
    progress_percentage = models.FloatField(default=0.0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        unique_together = ('user', 'tmdb_id', 'media_type')

    def __str__(self):
        return f"{self.user.username} - {self.media_type} {self.tmdb_id}"

class Watchlist(models.models):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlist')
    tmdb_id = models.IntegerField()
    media_type = models.CharField(max_length=10, choices=[('movie', 'Movie'), ('tv', 'TV Show')])
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-added_at']
        unique_together = ('user', 'tmdb_id', 'media_type')