from django.db import models
from django.contrib.auth.models import User

class WatchHistory(models.Model): # <-- Diperbaiki dari models.fields
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watch_history')
    tmdb_id = models.IntegerField()
    current_time_seconds = models.FloatField(default=0)
    total_duration = models.FloatField(null=True, blank=True)
    is_finished = models.BooleanField(default=False)
    media_type = models.CharField(max_length=10, choices=[('movie', 'Movie'), ('tv', 'TV Show')])
    progress_percentage = models.FloatField(default=0.0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        unique_together = ('user', 'tmdb_id', 'media_type')

    def __str__(self):
        return f"{self.user.username} - {self.media_type} {self.tmdb_id}"

class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    tmdb_id = models.IntegerField()
    media_type = models.CharField(max_length=10)

    title = models.CharField(max_length=255)
    poster_path = models.CharField(max_length=255, null=True, blank=True)
    backdrop_path = models.CharField(max_length=255, null=True, blank=True)

    rating = models.FloatField(null=True, blank=True)
    year = models.CharField(max_length=10, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)