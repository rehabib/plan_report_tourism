from django.db import models
from django.conf import settings
from .plan import BasePlan


class QuarterlyPlan(BasePlan):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    QUARTER_CHOICES = [(1, 'Q1'), (2, 'Q2'), (3, 'Q3'), (4, 'Q4')]

    quarter = models.IntegerField(choices=QUARTER_CHOICES)
    summary = models.TextField(blank=True, null=True)
    auto_aggregate = models.BooleanField(default=False)

    status = models.CharField(
        max_length=20,
        choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')],
        default='PENDING'
    )

    def __str__(self):
        return f"Quarterly Plan: {self.user.username} Q{self.quarter} {self.year} [{self.status}]"
