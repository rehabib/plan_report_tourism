from django.db import models
from .weekly_plan import WeeklyPlan
from .monthly_plan import MonthlyPlan
from .quarterly_plan import QuarterlyPlan
from .yearly_plan import YearlyPlan
from .goal import StrategicGoal


class Activity(models.Model):
    # Generic relation to any plan type (Weekly, Monthly, Quarterly, Yearly)
    weekly_plan = models.ForeignKey(WeeklyPlan, on_delete=models.CASCADE, related_name='weakly_activities', null=True, blank=True)
    monthly_plan = models.ForeignKey(MonthlyPlan, on_delete=models.CASCADE, related_name='monthly_activities', null=True, blank=True)
    quarterly_plan = models.ForeignKey(QuarterlyPlan, on_delete=models.CASCADE, related_name='quarterly_activities', null=True, blank=True)
    yearly_plan = models.ForeignKey(YearlyPlan, on_delete=models.CASCADE, related_name='yearly_activities', null=True, blank=True)
    goal = models.ForeignKey(StrategicGoal, on_delete=models.CASCADE, related_name='activities', null=True, blank=True)
    
    name = models.CharField(max_length=255, default="Unnamed Activity")
    
    major_activity = models.CharField(max_length=255)
    detail_activity = models.TextField()
    responsible_person = models.CharField(max_length=255)
    budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=[("PENDING", "Pending"), ("IN_PROGRESS", "In Progress"), ("COMPLETED", "Completed")],
        default="PENDING"
    )


    @property
    def plan(self):
        return self.weekly_plan or self.monthly_plan or self.quarterly_plan or self.yearly_plan

    def __str__(self):
        return f"Activity: {self.major_activity} ({self.plan})"
