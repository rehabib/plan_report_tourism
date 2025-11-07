from django.db import models
from django.conf import settings
from django.db.models import Sum

# Consolidated models into a single file for a clearer structure and easier management.

class Plan(models.Model):
    """
    Model representing a strategic plan for a specific period.
    The total budget is calculated as the sum of budgets from all Major Activities.
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

    @property
    def total_budget(self):
        """Calculates the total budget for the plan by summing up MajorActivity budgets."""
        # Use Sum aggregate function from Django DB
        return self.major_activities.aggregate(Sum('budget'))['budget__sum'] or 0

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
    measurement = models.CharField(max_length=255, help_text="e.g., Percentage, Count", null=True, blank=True)
    baseline = models.FloatField()
    target = models.FloatField()

    #New fields for Quaterly and Yearly Plans
    target_q1 = models.FloatField(default=0.0)
    target_q2 = models.FloatField(default=0.0)
    target_q3 = models.FloatField(default=0.0)
    target_q4 = models.FloatField(default=0.0)
    
    def __str__(self):
        return self.name

class MajorActivity(models.Model):
    """
    A high-level activity (the 'major activity') that holds the total
    allocated weight and budget, and acts as a container for DetailActivities.
    """
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='major_activities', null=True, blank=True)
    name = models.CharField(max_length=255, verbose_name="Major Activity Name")
    
    # This is the TOTAL weight allocated to this major activity
    total_weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="The total weight of this major activity. Detail activities' weights must sum up to this value.",
        null=True,
        blank=True
    )
    
    # This is the TOTAL budget allocated to this major activity
    budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Total budget for this major activity and all its sub-tasks.")

    def __str__(self):
        return f"Major Activity: {self.name} (Plan: {self.plan})"
    
    @property
    def current_detail_weight(self):
        """Calculates the sum of weights from all associated DetailActivities."""
        return self.detail_activities.aggregate(Sum('weight'))['weight__sum'] or 0

class DetailActivity(models.Model):
    """
    A smaller, actionable task (the 'detail activity') that belongs to a MajorActivity.
    Its weight is a sub-division of the MajorActivity's total_weight.
    """
    major_activity = models.ForeignKey(
        MajorActivity, 
        on_delete=models.CASCADE, 
        related_name='detail_activities',
        help_text="The major activity this detail activity belongs to."
    )
    
    description = models.TextField(verbose_name="Detail Activity Description")
    
    # This is the weight share of the major activity's total weight
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Weight share of the Major Activity's total weight."
    )
    
    responsible_person = models.CharField(max_length=255)

    status = models.CharField(
        max_length=20,
        choices=[("PENDING", "Pending"), ("IN_PROGRESS", "In Progress"), ("COMPLETED", "Completed")],
        default="PENDING"
    )

    def __str__(self):
        return f"Detail: {self.description[:50]}... (Major: {self.major_activity.name})"
    
    class Meta:
        verbose_name_plural = "Detail Activities"
        ordering = ['major_activity', 'weight']