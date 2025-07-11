from django.db import models
from .goal import StrategicGoal

class KPI(models.Model):
    goal = models.ForeignKey(StrategicGoal, on_delete=models.CASCADE, related_name='kpis')
    name = models.CharField(max_length=255)
    baseline = models.FloatField()
    unit = models.CharField(max_length=100)

    def __str__(self):
        return f"KPI: {self.name}"

class Target(models.Model):
    kpi = models.ForeignKey(KPI, on_delete=models.CASCADE, related_name='targets')
    yearly = models.FloatField(null=True, blank=True)
    quarterly = models.FloatField(null=True, blank=True)
    monthly = models.FloatField(null=True, blank=True)
    weekly = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Target for {self.kpi.name}"
