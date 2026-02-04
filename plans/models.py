from django.db import models
from django.conf import settings
from django.db.models import Sum
from plans.permissions import PLAN_APPROVAL_FLOW

# --- Base Models for Planning Structure ---

class Plan(models.Model):
    LEVEL_CHOICES = [
            
        ("individual", "Individual"),
        ("desk", "Desk"),
        ("department", "Department"),
        ("corporate", "Corporate"),
        ("state-minister-destination", "State Minister - Destination"),
        ("state-minister-promotion", "State Minister - Promotion"),
        ("strategic-team", "Strategic Team"),
        ("minister", "Minister"),
        
    ]

    PLAN_TYPE_CHOICES = [
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
        ("yearly", "Yearly"),
    ]

    WORKFLOW_STATUS = [
        ("DRAFT", "Draft"),
        ("SUBMITTED", "Submitted"),
        ("RESUBMITTED", "Resubmitted"),#for rejected plans
        ("IN_REVIEW", "In Review"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    level = models.CharField(max_length=40, choices=LEVEL_CHOICES)
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

    pillar = models.CharField(
        max_length=40,
        choices=[
            ("corporate", "Corporate"),
            ("state-minister-destination", "State Minister - Destination"),
            ("state-minister-promotion", "State Minister - Promotion"),
        ],
        null=True, blank=True

    )

    status = models.CharField(
    max_length=20,
    choices=WORKFLOW_STATUS,
    default="DRAFT"
)
    
    current_reviewer_role = models.CharField(
        max_length=40,
        blank=True,
        null=True
    )

    

    review_comments = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # PLAN_APPROVAL_FLOW = {
    #     "individual": "desk",
    #     "desk": "department",
    #     "department": "pillar",

    #     "corporate": "strategic-team",
    #     "state-minister-destination": "strategic-team",
    #     "state-minister-promotion": "strategic-team",

    #     "strategic-team": "minister",
    # }

    def can_user_view(self, user):
    #Owner always sees
        if self.user == user:
            return True

        #Current reviewer
        if user.role == self.current_reviewer_role:
            return True

        # Desk → Individual
        if user.role == "desk" and self.level == "individual":
            return True

        #Department → Desk + Individual (same department)
        if (
            user.role == "department"
            and self.user.department
            and user.department == self.user.department
            and self.level in ["desk", "individual"]
        ):
            return True

        # Pillar roles → Departments under that pillar
        if (
            user.role in [
                "corporate",
                "state-minister-destination",
                "state-minister-promotion",
            ]
            and self.user.department
            and self.user.department.pillar == user.role
        ):
            return True

        #Strategic team → all pillar plans
        if user.role == "strategic-team" and self.level in [
            "corporate",
            "state-minister-destination",
            "state-minister-promotion",
        ]:
            return True

        #Minister → strategic team plans
        if user.role == "minister" and self.level == "strategic-team":
            return True

        return False


    def can_user_edit(self, user):
        return (
            self.user == user and
            self.status in ["DRAFT", "REJECTED"]
        )

    def can_user_approve(self, user):
        return (
            self.status in ["SUBMITTED", "RESUBMITTED", "IN_REVIEW"] and
            user.role == self.current_reviewer_role
        )

    def move_to_next_reviewer(self):
        next_role = PLAN_APPROVAL_FLOW.get(self.level)

        if next_role == "pillar":
            next_role = self.pillar

        self.current_reviewer_role = next_role
        self.status = "IN_REVIEW"
        self.save()
    
    # def approve(self, user):
    #     if not self.can_user_approve(user):
    #         raise PermissionError("You cannot approve this plan.")

    #     next_role = PLAN_APPROVAL_FLOW.get(self.level)
    #     if next_role == "pillar":
    #         next_role = self.pillar

    #     if next_role:  # There’s another reviewer
    #         self.current_reviewer_role = next_role
    #         self.status = "IN_REVIEW"
    #     else:  # No next reviewer → final approval
    #         self.status = "APPROVED"
    #         self.current_reviewer_role = None
    #     self.save()

    def is_final_approver(self, user):
    
        FINAL_APPROVERS = {
            "individual": "department",
            "desk": "department",
            "department": "pillar",  # resolved dynamically
            "corporate": "strategic-team",
            "state-minister-destination": "strategic-team",
            "state-minister-promotion": "strategic-team",
            "strategic-team": "minister",
        }

        final_role = FINAL_APPROVERS.get(self.level)

        if final_role == "pillar":
            final_role = self.pillar

        return user.role == final_role

    def approve(self, user):
        if not self.can_user_approve(user):
            raise PermissionError("You cannot approve this plan.")

        # FINAL approval
        if self.is_final_approver(user):
            self.status = "APPROVED"
            self.current_reviewer_role = None
            self.save()
            return

        # Otherwise → move to next reviewer
        self.move_to_next_reviewer()

    def reject(self, user, comment=None):
        """Reject the plan if the user is the current reviewer."""
        if not self.can_user_approve(user):
            raise PermissionError("You cannot reject this plan.")

        self.status = "REJECTED"
        if comment:
            self.review_comments = comment
        self.current_reviewer_role = None
        self.save()

    

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
class Department(models.Model):
    PILLAR_CHOICES = [
        ("corporate", "Corporate"),
        ("state-minister-destination", "State Minister - Destination"),
        ("state-minister-promotion", "State Minister - Promotion"),
    ]

    name = models.CharField(max_length=100, unique=True)
    pillar = models.CharField(max_length=40, choices=PILLAR_CHOICES)

    def __str__(self):
        return f"{self.name} ({self.pillar})"
    

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
    weight = models.DecimalField(max_digits=5, decimal_places=2,default=0.00)
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
        return result["sum_weight"] or 0.00


class DetailActivity(models.Model):
    major_activity = models.ForeignKey(
        MajorActivity,
        on_delete=models.CASCADE,
        related_name="detail_activities"
    )

    detail_activity = models.TextField()
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
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
    
    