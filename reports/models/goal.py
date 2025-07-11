from django.db import models
from .plan import Plan

class StrategicGoal(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='goals')
    title = models.CharField(max_length=255)

    def __str__(self):
        return f"Goal: {self.title} ({self.plan.level})"


