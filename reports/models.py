from .utils import get_kpi_target
from django.db import models
from django.conf import settings
from plans.models import Plan, KPI, MajorActivity, DetailActivity
from django.db.models import Avg, Sum
#report part

class Report(models.Model):
    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("SUBMITTED", "Submitted"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    plan = models.ForeignKey(
        Plan,
        on_delete=models.CASCADE,
        related_name="reports"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    reporting_period = models.CharField(
        max_length=20,
        choices=Plan.PLAN_TYPE_CHOICES
    )

    submission_date = models.DateField(auto_now_add=True)

    overall_comment = models.TextField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="DRAFT"
    )

    reviewer_comment = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.plan} - {self.reporting_period} Report"

    @property
    def overall_progress(self):
        result = self.activity_reports.aggregate(avg=Avg("progress"))
        return round(result["avg"] or 0, 2)


class KPIReport(models.Model):
    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name="kpi_reports"
    )

    kpi = models.ForeignKey(
        KPI,
        on_delete=models.CASCADE
    )

    actual_value = models.FloatField()
    achievement_percent = models.FloatField(help_text="Calculated %")
    remark = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        plan = self.report.plan
        target = get_kpi_target(self.kpi, plan)

        if target and target > 0:
            self.achievement_percent = round(
                (self.actual_value / target) * 100, 2
            )
        else:
            self.achievement_percent = 0

        super().save(*args, **kwargs)


class MajorActivityReport(models.Model):
    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name="activity_reports"
    )

    major_activity = models.ForeignKey(
        MajorActivity,
        on_delete=models.CASCADE
    )

    progress = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Completion percentage"
    )

    actual_budget_used = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )

    challenge = models.TextField(blank=True, null=True)
    mitigation = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.major_activity.major_activity


class DetailActivityReport(models.Model):
    activity_report = models.ForeignKey(
        MajorActivityReport,
        on_delete=models.CASCADE,
        related_name="detail_reports"
    )

    detail_activity = models.ForeignKey(
        DetailActivity,
        on_delete=models.CASCADE
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ("NOT_STARTED", "Not Started"),
            ("IN_PROGRESS", "In Progress"),
            ("COMPLETED", "Completed"),
        ]
    )

    comment = models.TextField(blank=True, null=True)
