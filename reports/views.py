from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction

from plans.models import Plan
from .models import Report, KPIReport, MajorActivityReport
from .forms import (
    ReportForm,
    KPIReportFormSet,
    MajorActivityReportFormSet,
)


@login_required
def create_report(request, plan_id):
    plan = get_object_or_404(
        Plan,
        id=plan_id,
        status="APPROVED"
    )

    report, _ = Report.objects.get_or_create(
        plan=plan,
        user=request.user,
        reporting_period=plan.plan_type
    )

    # 🔹 Auto-create KPI report rows
    for kpi in plan.kpis.all():
        KPIReport.objects.get_or_create(
            report=report,
            kpi=kpi
        )

    # 🔹 Auto-create major activity report rows
    for activity in plan.major_activities.all():
        MajorActivityReport.objects.get_or_create(
            report=report,
            major_activity=activity
        )

    if request.method == "POST":
        form = ReportForm(request.POST, instance=report)

        kpi_formset = KPIReportFormSet(
            request.POST,
            instance=report,
            plan=plan
        )

        activity_formset = MajorActivityReportFormSet(
            request.POST,
            instance=report
        )

        if (
            form.is_valid()
            and kpi_formset.is_valid()
            and activity_formset.is_valid()
        ):
            with transaction.atomic():
                form.save()
                kpi_formset.save()
                activity_formset.save()

                report.status = "SUBMITTED"
                report.save()

            return redirect("view_report", report.id)

    else:
        form = ReportForm(instance=report)

        kpi_formset = KPIReportFormSet(
            instance=report,
            plan=plan
        )

        activity_formset = MajorActivityReportFormSet(
            instance=report
        )

    return render(
        request,
        "reports/create_report.html",
        {
            "plan": plan,
            "report": report,
            "form": form,
            "kpi_formset": kpi_formset,
            "activity_formset": activity_formset,
        },
    )

@login_required
def view_report(request, report_id):
    report = get_object_or_404(
        Report,
        id=report_id,
        user=request.user
    )

    return render(
        request,
        "reports/view_report.html",
        {
            "report": report,
            "kpi_reports": report.kpi_reports.select_related("kpi"),
            "activity_reports": report.activity_reports.select_related("major_activity"),
        }
    )
