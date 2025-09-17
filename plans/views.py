import re
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q
from django.http import Http404 # Import Http404 to manually raise the error
from .models import Plan, StrategicGoal, KPI, Activity
from .forms import PlanCreationForm, StrategicGoalFormset, KPIFormset, ActivityFormset
from accounts.models import User


def user_login(request):
    """
    Handles user login with the built-in authentication form.
    Correctly renders the auth.html template from the accounts app.
    """
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    # Pass 'view_name' to the template to tell it which title to display
    return render(request, 'accounts/auth.html', {'form': form, 'view_name': 'login'})


@login_required
def user_logout(request):
    """
    Handles user logout.
    """
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    """
    Displays the dashboard with plans based on the user's role and selected filter.
    Uses prefetch_related for optimal performance.
    """
    user_role = request.user.role.lower()
    plans = Plan.objects.none()

    # Get the show and department parameters from the URL to filter the plans
    show_my_plans = request.GET.get('show', 'all') == 'my_plans'
    selected_department_name = request.GET.get('department', '')

    # Prefetch all related fields directly from the Plan model
    # The related names are 'goals', 'kpis', and 'activities'
    prefetch_fields = ('goals', 'kpis', 'activities')
    
    # Base query for all plans, excluding any filtering by user for now
    base_query = Plan.objects.all().prefetch_related(*prefetch_fields).order_by('-year', '-month', '-week_number')

    # New, corrected logic: check for 'my_plans' filter first for all users
    if show_my_plans:
        plans = base_query.filter(user=request.user)
    elif user_role == 'corporate':
        # Corporate users can see all plans by default or filter by department
        if selected_department_name:
            plans = base_query.filter(user__department__iexact=selected_department_name)
        else:
            plans = base_query
    elif user_role == 'department':
        # Department users can see their own plans and all individual plans within their department
        plans = base_query.filter(
            Q(user=request.user) | Q(level__iexact='individual', user__department=request.user.department)
        )
    elif user_role == 'individual':
        # Individual users can only see their own plans
        plans = base_query.filter(user=request.user)

    all_departments = []
    if user_role == 'corporate':
        # Get a unique list of department names for the corporate user filter
        all_departments = User.objects.filter(department__isnull=False).values_list('department', flat=True).distinct()

    context = {
        'user_role': user_role,
        'plans': plans,
        'show_my_plans': show_my_plans,
        'all_departments': all_departments,
        'selected_department': selected_department_name,
    }
    return render(request, 'plans/dashboard.html', context)


@login_required
def create_plan(request):
    """
    Handles the creation of a new plan and its related goals, KPIs, and activities.
    """
    if request.method == 'POST':
        form = PlanCreationForm(request.POST)
        goal_formset = StrategicGoalFormset(request.POST, prefix='goals')
        kpi_formset = KPIFormset(request.POST, prefix='kpis')
        activity_formset = ActivityFormset(request.POST, prefix='activities')

        if form.is_valid() and goal_formset.is_valid() and kpi_formset.is_valid() and activity_formset.is_valid():
            # Save the main Plan object
            plan = form.save(commit=False)
            plan.user = request.user
            plan.level = request.user.role.lower()
            plan.save()

            # Save the formsets
            goal_formset.instance = plan
            goal_formset.save()
            
            kpi_formset.instance = plan
            kpi_formset.save()
            
            activity_formset.instance = plan
            activity_formset.save()

            # Corrected line: Redirect to the plan_success view, passing the new plan's ID
            return redirect('plan_success', plan_id=plan.id)
    else:
        form = PlanCreationForm()
        goal_formset = StrategicGoalFormset(prefix='goals')
        kpi_formset = KPIFormset(prefix='kpis')
        activity_formset = ActivityFormset(prefix='activities')

    context = {
        'form': form,
        'goal_formset': goal_formset,
        'kpi_formset': kpi_formset,
        'activity_formset': activity_formset,
    }
    return render(request, 'plans/create_plan.html', context)


@login_required
def edit_plan(request, plan_id):
    """
    Handles the editing of an existing plan and its related goals, KPIs, and activities.
    """
    plan = get_object_or_404(Plan, id=plan_id)
    # Check if the user has permission to edit this plan
    if plan.user != request.user:
        raise Http404("You do not have permission to edit this plan.")

    if request.method == 'POST':
        form = PlanCreationForm(request.POST, instance=plan)
        goal_formset = StrategicGoalFormset(request.POST, instance=plan, prefix='goals')
        kpi_formset = KPIFormset(request.POST, instance=plan, prefix='kpis')
        activity_formset = ActivityFormset(request.POST, instance=plan, prefix='activities')

        if form.is_valid() and goal_formset.is_valid() and kpi_formset.is_valid() and activity_formset.is_valid():
            # Save the main Plan object
            plan = form.save()

            # The formset.save() method automatically handles creating new objects,
            # updating existing ones, and deleting those marked with the DELETE checkbox.
            goal_formset.save()
            kpi_formset.save()
            activity_formset.save()

            return redirect('dashboard')
    else:
        form = PlanCreationForm(instance=plan)
        goal_formset = StrategicGoalFormset(instance=plan, prefix='goals')
        kpi_formset = KPIFormset(instance=plan, prefix='kpis')
        activity_formset = ActivityFormset(instance=plan, prefix='activities')

    context = {
        'form': form,
        'goal_formset': goal_formset,
        'kpi_formset': kpi_formset,
        'activity_formset': activity_formset,
    }
    return render(request, 'plans/create_plan.html', context)


@login_required
def plan_success(request, plan_id):
    """
    Renders the success page after a plan is created.
    """
    return render(request, 'plans/plan_success.html', {'plan_id': plan_id})
    

@login_required
def view_plan(request, plan_id):
    """
    Displays the details of a specific plan with proper access control based on user role.
    """
    # First, get the plan regardless of the user
    plan = get_object_or_404(Plan, id=plan_id)
    
    # Now, implement access control logic
    user_role = request.user.role.lower()
    can_view = False

    # A corporate user can view any plan
    if user_role == 'corporate':
        can_view = True
    # A department user can view plans within their department or their own plans
    elif user_role == 'department':
        if plan.user.department == request.user.department:
            can_view = True
    # An individual user can only view their own plans
    elif plan.user == request.user:
        can_view = True
    
    # If the user doesn't have permission, raise a 404 error
    if not can_view:
        raise Http404("You do not have permission to view this plan.")

    goals = StrategicGoal.objects.filter(plan=plan)
    kpis = KPI.objects.filter(plan=plan)
    activities = Activity.objects.filter(plan=plan)
    
    context = {
        'plan': plan,
        'goals': goals,
        'kpis': kpis,
        'activities': activities,
    }
    return render(request, 'plans/view_plan.html', context)
    

@login_required
def delete_plan(request, plan_id):
    """
    Deletes a specific plan based on its ID.
    The view only processes POST requests for security reasons.
    """
    plan_to_delete = get_object_or_404(Plan, pk=plan_id)
    
    # Check if the request method is POST.
    if request.method == 'POST':
        plan_to_delete.delete()
        # Redirect the user back to the dashboard or a success page.
        return redirect('dashboard') 

    # If it's a GET request, you could show a confirmation page.
    # For now, we'll just redirect to avoid showing an empty page.
    return redirect('dashboard')
