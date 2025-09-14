from django.db import models
from django.conf import settings

# Consolidated models into a single file for a clearer structure and easier management.
# This avoids issues with circular imports between models in separate files.

class Plan(models.Model):
    """
    Model representing a strategic plan for a specific period.
    """
    LEVEL_CHOICES = [
        ("individual", "Individual"),
        ("department", "Department"),
        ("corporate", "Corporate"),
    ]

    PLAN_TYPE_CHOICES = [
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
        ("yearly", "Yearly"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPE_CHOICES)
    year = models.PositiveIntegerField()

    week_number = models.PositiveSmallIntegerField(
        choices=[(i, f"Week {i}") for i in range(1, 5)],
        null=True, blank=True
    )
    MONTH_CHOICES = [
        (1, "July"), (2, "August"), (3, "September"), (4, "October"),
        (5, "November"), (6, "December"), (7, "January"), (8, "February"),
        (9, "March"), (10, "April"), (11, "May"), (12, "June")
    ]

    month = models.PositiveSmallIntegerField(
        choices=MONTH_CHOICES,
        null=True,
        blank=True
    )


    
    quarter_number = models.PositiveSmallIntegerField(
        choices=[(i, f"Quarter {i}") for i in range(1, 5)],
        null=True, blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=[("PENDING", "Pending"), ("APPROVED", "Approved"), ("REJECTED", "Rejected")],
        default="PENDING"
    )
    review_comments = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        extra = ""
        if self.plan_type == "weekly" and self.week_number:
            extra = f" - Week {self.week_number}"
        elif self.plan_type == "monthly" and self.month:
            extra = f" - Month {self.month}"
        elif self.plan_type == "quarterly" and self.quarter_number:
            extra = f" - Quarter {self.quarter_number}"
        return f"{self.level.title()} {self.plan_type.title()} Plan {self.year}{extra}"

class StrategicGoal(models.Model):
    """
    A strategic goal linked to a plan.
    """
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name="goals", null=True, blank=True)
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title

class KPI(models.Model):
    """
    A Key Performance Indicator linked to a plan.
    """
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name="kpis", null=True, blank=True)
    name = models.CharField(max_length=255)
    baseline = models.FloatField()
    target = models.FloatField()

    def __str__(self):
        return self.name

class Activity(models.Model):
    """
    A specific activity to achieve a goal.
    """
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='activities', null=True, blank=True)
    #goal = models.ForeignKey(StrategicGoal, on_delete=models.CASCADE, related_name='activities', null=True, blank=True)
    major_activity = models.CharField(max_length=255)
    detail_activity = models.TextField()
    responsible_person = models.CharField(max_length=255)
    budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=[("PENDING", "Pending"), ("IN_PROGRESS", "In Progress"), ("COMPLETED", "Completed")],
        default="PENDING"
    )

    def __str__(self):
        return f"Activity: {self.major_activity} ({self.plan})"
