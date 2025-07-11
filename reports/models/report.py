from django.db import models
from django.contrib.auth.models import User
from .plan import Plan

class Report(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='reports')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report by {self.user.username} for {self.plan.level}"
