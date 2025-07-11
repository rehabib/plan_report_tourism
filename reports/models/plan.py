from django.db import models
from django.contrib.auth.models import User

class Plan(models.Model):
    LEVEL_CHOICES = [
        ('CORPORATE', 'Corporate'),
        ('DEPARTMENT', 'Department'),
        ('TEAM', 'Team/Desk'),
        ('INDIVIDUAL', 'Individual'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    year = models.PositiveIntegerField()
    quarter = models.CharField(max_length=10, blank=True, null=True)
    month = models.CharField(max_length=10, blank=True, null=True)
    week = models.CharField(max_length=10, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.level} Plan - {self.user.username} ({self.year})"
