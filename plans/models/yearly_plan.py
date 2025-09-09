from django.db import models
from django.conf import settings
from .plan import BasePlan


class YearlyPlan(BasePlan):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    summary = models.TextField(blank=True, null=True)
    auto_aggregate = models.BooleanField(default=False)

    status = models.CharField(
        max_length=20,
        choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')],
        default='PENDING'
    )

    def __str__(self):
        return f"Yearly Plan: {self.user.username} {self.year} [{self.status}]"
