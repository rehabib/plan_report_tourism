from django.db import models
from django.conf import settings
from .plan import BasePlan


class WeeklyPlan(BasePlan):
    kpi = models.TextField(blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    WEEK_CHOICES = [(i, f'Week {i}') for i in range(1, 5)]

    week_number = models.IntegerField(choices=WEEK_CHOICES)
    month = models.CharField(max_length=15, null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')],
        default='PENDING'
    )
    review_comments = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Weekly Plan: {self.user.username} Week {self.week_number} ({self.month}/{self.year}) [{self.status}]"
