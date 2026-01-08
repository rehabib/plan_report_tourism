from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from plans.models import Plan
from .models import Report, KPIReport, MajorActivityReport
from .forms import ReportForm, KPIReportFormSet, MajorActivityReportFormSet



@login_required
def create_report(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id, status="APPROVED")

    report, created = Report.objects.get_or_create(
        plan=plan,
        user=request.user,
        reporting_period=plan.plan_type
    )

    if request.method == "POST":
        form = ReportForm(request.POST, instance=report)
        kpi_formset = KPIReportFormSet(request.POST, instance=report)
        activity_formset = MajorActivityReportFormSet(request.POST, instance=report)

        if form.is_valid() and kpi_formset.is_valid() and activity_formset.is_valid():
            with transaction.atomic():
                form.save()
                kpi_formset.save()
                activity_formset.save()
                report.status = "SUBMITTED"
                report.save()
            return redirect("view_report", report.id)

    else:
        form = ReportForm(instance=report)

        # Auto-create KPI & activity report rows
        for kpi in plan.kpis.all():
            KPIReport.objects.get_or_create(report=report, kpi=kpi)

        for act in plan.major_activities.all():
            MajorActivityReport.objects.get_or_create(
                report=report,
                major_activity=act
            )

        kpi_formset = KPIReportFormSet(instance=report)
        activity_formset = MajorActivityReportFormSet(instance=report)

    return render(request, "reports/create_report.html", {
        "plan": plan,
        "form": form,
        "kpi_formset": kpi_formset,
        "activity_formset": activity_formset,
    })



