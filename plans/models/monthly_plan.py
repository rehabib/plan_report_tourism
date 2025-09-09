from django.db import models
from django.conf import settings
from .plan import BasePlan


class MonthlyPlan(BasePlan):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    MONTH_CHOICES = [
        ('January', 'January'), ('February', 'February'), ('March', 'March'),
        ('April', 'April'), ('May', 'May'), ('June', 'June'),
        ('July', 'July'), ('August', 'August'), ('September', 'September'),
        ('October', 'October'), ('November', 'November'), ('December', 'December'),
    ]

    month = models.CharField(max_length=15, choices=MONTH_CHOICES)
    summary = models.TextField(blank=True, null=True)
    auto_aggregate = models.BooleanField(default=False)

    status = models.CharField(
        max_length=20,
        choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')],
        default='PENDING'
    )
    review_comments = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Monthly Plan: {self.user.username} {self.month} {self.year} [{self.status}]"
