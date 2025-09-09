# models/kpi.py
from django.db import models
from .weekly_plan import WeeklyPlan
from .monthly_plan import MonthlyPlan
from .quarterly_plan import QuarterlyPlan
from .yearly_plan import YearlyPlan
from .goal import StrategicGoal

class KPI(models.Model):
    weekly_plan = models.ForeignKey(WeeklyPlan, on_delete=models.CASCADE, related_name='weekly_kpis', null=True, blank=True)
    monthly_plan = models.ForeignKey(MonthlyPlan, on_delete=models.CASCADE, related_name='monthly_kpis', null=True, blank=True)
    quarterly_plan = models.ForeignKey(QuarterlyPlan, on_delete=models.CASCADE, related_name='quarterly_kpis', null=True, blank=True)
    yearly_plan = models.ForeignKey(YearlyPlan, on_delete=models.CASCADE, related_name='yearly_kpis', null=True, blank=True)
    goal = models.ForeignKey(StrategicGoal, on_delete=models.CASCADE, related_name='kpis')
    
    name = models.CharField(max_length=255)
    baseline = models.CharField(max_length=255)
    target = models.CharField(max_length=255)
    accountable_person = models.CharField(max_length=255)
    budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"KPI: {self.name}"
