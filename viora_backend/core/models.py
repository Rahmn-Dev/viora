from django.db import models
from django.contrib.auth.models import User

class WatchHistory(models.Model): # <-- Diperbaiki dari models.fields
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watch_history')
    tmdb_id = models.IntegerField()
    season = models.IntegerField(null=True, blank=True)
    episode = models.IntegerField(null=True, blank=True)
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


class VIPSubscription(models.Model):
    PLAN_CHOICES = [
        ('admin', '👑 VIP Supreme Admin Pass (Ultimate Access)'),
        ('annual', '⭐ VIP Annual Pass (1 Year Access)'),
        ('monthly', '🌙 VIP Monthly Pass (1 Month Access)'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vip_subscription', null=True, blank=True)
    checkout_token = models.CharField(max_length=100, unique=True, null=True, blank=True)
    is_claimed = models.BooleanField(default=False)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='annual')
    invoice_no = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, default='PAID')
    payment_gateway = models.CharField(max_length=50, default='Xendit Official Gateway')
    amount_paid = models.CharField(max_length=50, default='$11.99 USD')
    valid_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'VIP Subscription & Invoice'
        verbose_name_plural = 'VIP Subscriptions & Invoices'
        ordering = ['-created_at']

    def __str__(self):
        username = self.user.username if self.user else "Anonymous (Pending)"
        return f"{username} - {self.get_plan_display()} ({self.invoice_no})"