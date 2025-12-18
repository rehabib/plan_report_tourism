from django.db import models
from django.conf import settings
from django.db.models import Sum

# --- Base Models for Planning Structure ---

class Plan(models.Model):
    LEVEL_CHOICES = [
        ("individual", "Individual"),
        ("desk", "Desk"),
        ("department", "Department"),
        ("md", "MD"),
        ("corporate", "Corporate"),
        ("strategic-team", "Strategic Team")
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

    # Timeframe
    week_number = models.PositiveSmallIntegerField(
        choices=[(i, f"Week {i}") for i in range(1, 53)],
        null=True, blank=True
    )

    MONTH_CHOICES = [
        (1, "July"), (2, "August"), (3, "September"), (4, "October"),
        (5, "November"), (6, "December"), (7, "January"), (8, "February"),
        (9, "March"), (10, "April"), (11, "May"), (12, "June")
    ]
    month = models.PositiveSmallIntegerField(choices=MONTH_CHOICES, null=True, blank=True)

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
            extra = f" - Month {dict(self.MONTH_CHOICES).get(self.month)}"
        elif self.plan_type == "quarterly" and self.quarter_number:
            extra = f" - Quarter {self.quarter_number}"
        return f"{self.level.title()} {self.plan_type.title()} Plan {self.year}{extra}"

    @property
    def total_budget(self):
        """Calculates the total budget from all associated Major Activities."""
        # Use aggregate for efficient database calculation
        result = self.major_activities.aggregate(total_budget=Sum("budget"))
        return result["total_budget"] or 0.00
# --- Plan Detail Models ---

class StrategicGoal(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name="goals", null=True, blank=True)
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title


class KPI(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name="kpis", null=True, blank=True)
    name = models.CharField(max_length=255)
    measurement = models.CharField(max_length=255, null=True, blank=True)
    baseline = models.FloatField()
    target = models.FloatField()

    target_q1 = models.FloatField(default=0.0)
    target_q2 = models.FloatField(default=0.0)
    target_q3 = models.FloatField(default=0.0)
    target_q4 = models.FloatField(default=0.0)

    def __str__(self):
        return self.name


# --- Activity Models ---

class MajorActivity(models.Model):
    plan = models.ForeignKey(
        Plan,
        on_delete=models.CASCADE,
        related_name="major_activities",
        null=True,
        blank=True
    )

    major_activity = models.CharField(max_length=255)
    weight = models.DecimalField(max_digits=5, decimal_places=2)
    budget = models.DecimalField(
    max_digits=10, 
    decimal_places=2, 
    default=0.00,
    help_text="Allocated budget for this Major Activity."
) 

    responsible_person = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
 

    def __str__(self):
        return f"{self.major_activity}"

    @property
    def total_weight(self):
       result = self.detail_activities.aggregate(sum_weight=Sum("weight"))
        # Returns 0 if no detail activities exist
       return result["sum_weight"] or 0.00


class DetailActivity(models.Model):
    major_activity = models.ForeignKey(
        MajorActivity,
        on_delete=models.CASCADE,
        related_name="detail_activities"
    )

    detail_activity = models.TextField()
    weight = models.DecimalField(max_digits=5, decimal_places=2)  
    responsible_person = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ("PENDING", "Pending"),
            ("IN_PROGRESS", "In Progress"),
            ("COMPLETED", "Completed")
        ],
        default="PENDING"
    )

    class Meta:
        ordering = ["major_activity", "weight"]
        verbose_name_plural = "Detail Activities"

    def __str__(self):
        # Ensure we handle short detail activities without slicing error
        description = self.detail_activity
        return f"Detail: {description[:50]}{'...' if len(description) > 50 else ''}"