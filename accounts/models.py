from django.db import models
from django.contrib.auth.models import User

AVATAR_COLORS = ['#6366f1', '#8b5cf6', '#ec4899', '#14b8a6', '#f59e0b', '#10b981', '#3b82f6', '#f97316']


class UserProfile(models.Model):
    ROLE_CHOICES = [('admin', 'Admin'), ('member', 'Member')]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    bio = models.TextField(blank=True)

    class Meta:
        ordering = ['user__username']

    def __str__(self):
        return f"{self.user.username}'s profile"

    @property
    def is_admin(self):
        return self.role == 'admin' or self.user.is_superuser

    @property
    def avatar_color(self):
        return AVATAR_COLORS[sum(ord(c) for c in self.user.username) % len(AVATAR_COLORS)]

    @property
    def display_name(self):
        full = f"{self.user.first_name} {self.user.last_name}".strip()
        return full or self.user.username

    @property
    def initials(self):
        fn = self.user.first_name
        ln = self.user.last_name
        if fn and ln:
            return (fn[0] + ln[0]).upper()
        return self.user.username[:2].upper()
