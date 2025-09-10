from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import ReportCreationForm
from plans.models import Plan
from .models import Report

@login_required
def create_report(request, plan_id):
    """
    Handles the creation of a new report for a given plan.
    """
    plan = get_object_or_404(Plan, pk=plan_id)

    # Security check to ensure the user has permission to report on this plan
    user_role = request.user.role.lower()
    has_permission = False
    if user_role == 'corporate' or user_role == 'department' or plan.user == request.user:
        has_permission = True
    
    if not has_permission:
        # Redirect or show an error if the user doesn't have permission
        return redirect('dashboard') # Or render a permission denied page

    if request.method == 'POST':
        form = ReportCreationForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.plan = plan
            # Set other fields like goal, kpi based on form and plan data
            report.save()
            return redirect('dashboard') # Redirect to dashboard or a reports list page
    else:
        # Pre-populate the plan field for convenience
        form = ReportCreationForm(initial={'plan': plan})

    context = {
        'form': form,
        'plan': plan,
    }
    return render(request, 'reports/create_report.html', context)

@login_required
def list_reports(request):
    """
    Displays a list of reports based on the user's role.
    """
    user_role = request.user.role.lower()
    reports = Report.objects.none()

    if user_role == 'corporate':
        reports = Report.objects.all().order_by('-created_at')
    elif user_role == 'department':
        # Department can see their own plan's reports and all individual reports
        reports = Report.objects.filter(
            Q(plan__user=request.user) | Q(plan__level='individual')
        ).order_by('-created_at')
    elif user_role == 'individual':
        reports = Report.objects.filter(plan__user=request.user).order_by('-created_at')

    context = {
        'reports': reports,
        'user_role': user_role
    }
    return render(request, 'reports/list_reports.html', context)
