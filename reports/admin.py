from django.contrib import admin
from django.contrib import admin
from .models import Report, KPIReport, MajorActivityReport, DetailActivityReport


class KPIReportInline(admin.TabularInline):
    model = KPIReport
    extra = 0


class MajorActivityReportInline(admin.TabularInline):
    model = MajorActivityReport
    extra = 0


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        "plan",
        "user",
        "reporting_period",
        "status",
        "submission_date",
    )
    list_filter = ("status", "reporting_period")
    search_fields = ("plan__title", "user__username")
    inlines = [KPIReportInline, MajorActivityReportInline]


@admin.register(KPIReport)
class KPIReportAdmin(admin.ModelAdmin):
    list_display = ("report", "kpi", "actual_value", "achievement_percent")


@admin.register(MajorActivityReport)
class MajorActivityReportAdmin(admin.ModelAdmin):
    list_display = ("report", "major_activity", "progress")


@admin.register(DetailActivityReport)
class DetailActivityReportAdmin(admin.ModelAdmin):
    list_display = ("activity_report", "detail_activity", "status")
