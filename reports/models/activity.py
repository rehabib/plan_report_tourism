from django.db import models
from .plan import Plan

class Activity(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='activities')
    major_activity = models.CharField(max_length=255)
    detail_activity = models.TextField()

    def __str__(self):
        return f"Activity: {self.major_activity} ({self.plan.level})"
