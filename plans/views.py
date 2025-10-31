import re
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q
from django.http import Http404 
from .models import Plan, StrategicGoal, KPI, Activity
from django.forms import inlineformset_factory
from .forms import PlanCreationForm, StrategicGoalFormset, KPIFormset, ActivityFormset
from accounts.models import User


def user_login(request):
    """
    Handles user login with the built-in authentication form.
    """
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
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
    """
    user_role = request.user.role.lower()
    prefetch_fields = ('goals', 'kpis', 'activities')
    base_query = Plan.objects.all().prefetch_related(*prefetch_fields).order_by('-year', '-month', '-week_number')

    show_my_plans = request.GET.get('show', 'all') == 'my_plans'
    selected_department_name = request.GET.get('department', '')

    if show_my_plans:
        plans = base_query.filter(user=request.user)
    elif user_role == 'corporate':
        if selected_department_name:
            plans = base_query.filter(user__department__iexact=selected_department_name)
        else:
            plans = base_query
    elif user_role == 'department':
        plans = base_query.filter(
            Q(user=request.user) | Q(level__iexact='individual', user__department=request.user.department)
        )
    elif user_role == 'individual':
        plans = base_query.filter(user=request.user)
    else:
        plans = Plan.objects.none() # Default safety

    all_departments = []
    if user_role == 'corporate':
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
    Handles the creation of a new plan, passing plan_type to KPI formset for validation.
    """
    if request.method == 'POST':
        form = PlanCreationForm(request.POST)

        # 1. Determine plan_type from POST data for formset validation
        plan_type = None
        formset_kwargs = {}

        if form.is_valid():
            # If the main form is valid, use the user-selected plan_type
            plan_type = form.cleaned_data.get('plan_type')
            formset_kwargs = {'plan_type': plan_type}
        
        # 2. Instantiate formsets, passing the plan_type to KPIFormset
        goal_formset = StrategicGoalFormset(request.POST, prefix='goals')
        kpi_formset = KPIFormset(request.POST, prefix='kpis', form_kwargs=formset_kwargs) # <-- CRITICAL CHANGE
        activity_formset = ActivityFormset(request.POST, prefix='activities')

        if form.is_valid() and goal_formset.is_valid() and kpi_formset.is_valid() and activity_formset.is_valid():
            plan = form.save(commit=False)
            plan.user = request.user
            plan.level = request.user.role.lower()
            plan.save()

            goal_formset.instance = plan
            goal_formset.save()
            
            kpi_formset.instance = plan
            kpi_formset.save()
            
            activity_formset.instance = plan
            activity_formset.save()

            return redirect('plan_success', plan_id=plan.id)
    else:
        # GET request: formsets use default 'yearly' plan_type in form.py
        form = PlanCreationForm()
        goal_formset = StrategicGoalFormset(prefix='goals')
        kpi_formset = KPIFormset(prefix='kpis')
        activity_formset = ActivityFormset(prefix='activities')

    context = {
        'form': form,
        'goal_formset': goal_formset,
        'kpi_formset': kpi_formset,
        'activity_formset': activity_formset,
        'plan_instance': None, # Indicates 'Create' mode
    }
    return render(request, 'plans/create_plan.html', context)


@login_required
def edit_plan(request, plan_id):
    """
    Handles the editing of an existing plan and its related goals, KPIs, and activities.
    Passes the existing or posted plan_type to the KPI formset.
    """
    plan = get_object_or_404(Plan, id=plan_id)
    
    if plan.user != request.user:
        raise Http404("You do not have permission to edit this plan.")

    if request.method == 'POST':
        form = PlanCreationForm(request.POST, instance=plan)
        
        # 1. Determine plan_type based on POST data or existing instance
        plan_type = None
        if form.is_valid():
            # Use POST data if valid
            plan_type = form.cleaned_data.get('plan_type')
        elif plan.plan_type:
            # Fallback to existing plan_type if POST is invalid
             plan_type = plan.plan_type
             
        formset_kwargs = {'plan_type': plan_type} if plan_type else {}

        # 2. Instantiate formsets, passing the plan_type to KPIFormset
        goal_formset = StrategicGoalFormset(request.POST, instance=plan, prefix='goals')
        kpi_formset = KPIFormset(request.POST, instance=plan, prefix='kpis', form_kwargs=formset_kwargs) # <-- CRITICAL CHANGE
        activity_formset = ActivityFormset(request.POST, instance=plan, prefix='activities')

        if form.is_valid() and goal_formset.is_valid() and kpi_formset.is_valid() and activity_formset.is_valid():
            form.save()
            goal_formset.save()
            kpi_formset.save()
            activity_formset.save()

            return redirect('dashboard')
    else:
        # GET request
        form = PlanCreationForm(instance=plan)
        
        # 1. Get the existing plan_type from the instance
        plan_type = plan.plan_type
        formset_kwargs = {'plan_type': plan_type} if plan_type else {}

        # 2. Instantiate formsets with existing instance and plan_type
        goal_formset = StrategicGoalFormset(instance=plan, prefix='goals')
        kpi_formset = KPIFormset(instance=plan, prefix='kpis', form_kwargs=formset_kwargs) # <-- CRITICAL CHANGE
        activity_formset = ActivityFormset(instance=plan, prefix='activities')

    context = {
        'form': form,
        'goal_formset': goal_formset,
        'kpi_formset': kpi_formset,
        'activity_formset': activity_formset,
        'plan_instance': plan, 
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
    Displays the details of a specific plan with proper access control.
    """
    plan = get_object_or_404(Plan, id=plan_id)
    
    user_role = request.user.role.lower()
    can_view = False

    if user_role == 'corporate' or (plan.user == request.user) or \
       (user_role == 'department' and plan.user.department == request.user.department):
        can_view = True
    
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
    Deletes a specific plan.
    """
    plan_to_delete = get_object_or_404(Plan, pk=plan_id)
    
    if request.method == 'POST':
        if plan_to_delete.user == request.user:
            plan_to_delete.delete()
        return redirect('dashboard') 

    return redirect('dashboard')
