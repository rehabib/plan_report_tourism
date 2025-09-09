from django.db import models
from django.contrib.auth.models import User


class BasePlan(models.Model):
    """
    Abstract base plan. Extended by WeeklyPlan, MonthlyPlan, QuarterlyPlan, YearlyPlan.
    'level' means who is responsible for the plan (Corporate, Department, Individual).
    """
    LEVEL_CHOICES = [
        ('CORPORATE', 'Corporate'),
        ('DEPARTMENT', 'Department'),
        ('INDIVIDUAL', 'Individual'),
    ]

    PLAN_TYPE_CHOICES = [
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('YEARLY', 'Yearly'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPE_CHOICES)
    year = models.PositiveIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.__class__.__name__} by {self.user.username} ({self.year})"
