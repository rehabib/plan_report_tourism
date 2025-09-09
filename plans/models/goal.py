from django.db import models
from .weekly_plan import WeeklyPlan
from .monthly_plan import MonthlyPlan
from .quarterly_plan import QuarterlyPlan
from .yearly_plan import YearlyPlan


class StrategicGoal(models.Model):
    weekly_plan = models.ForeignKey(WeeklyPlan, on_delete=models.CASCADE, related_name='weekly_goals', null=True, blank=True)
    monthly_plan = models.ForeignKey(MonthlyPlan, on_delete=models.CASCADE, related_name='monthly_goals', null=True, blank=True)
    quarterly_plan = models.ForeignKey(QuarterlyPlan, on_delete=models.CASCADE, related_name='quarterly_goals', null=True, blank=True)
    yearly_plan = models.ForeignKey(YearlyPlan, on_delete=models.CASCADE, related_name='goals', null=True, blank=True)
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Goal: {self.title} ({self.plan})"
