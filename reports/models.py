from django.db import models
from plans.models import Plan, StrategicGoal, KPI

class Report(models.Model):
    """
    Model for a report linked to a plan.
    """
    REPORT_TYPE_CHOICES = [ 
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
        ("yearly", "Yearly"),
    ]

    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name="reports")
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    date = models.DateField(null=True, blank=True)
    period = models.CharField(max_length=50, null=True, blank=True)

    goal = models.ForeignKey(StrategicGoal, on_delete=models.SET_NULL, null=True, blank=True, related_name="reports")
    kpi = models.ForeignKey(KPI, on_delete=models.SET_NULL, null=True, blank=True, related_name="reports")

    goal_title = models.CharField(max_length=255, blank=True, null=True)
    measurement_name = models.CharField(max_length=255, blank=True, null=True)
    baseline_value = models.FloatField(default=0.0)
    target_value = models.FloatField(default=0.0)
    achieved_value = models.FloatField(default=0.0)

    budget_planned = models.FloatField(default=0.0)
    budget_used = models.FloatField(default=0.0)

    performance = models.FloatField(default=0.0)
    difference = models.FloatField(default=0.0)

    responsible_body = models.CharField(max_length=255, blank=True, null=True)
    comment = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.report_type.capitalize()} Report for {self.plan}"
