import re
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q
from django.http import Http404
from django.forms import inlineformset_factory
from django.db import transaction # Important for atomic nested saves
from .models import Plan, StrategicGoal, KPI, MajorActivity, DetailActivity
from .forms import (
    PlanCreationForm, 
    StrategicGoalFormset, 
    KPIFormset, 
    MajorActivityFormset, 
    DetailActivityForm, # <-- Needed to instantiate individual Detail forms
    DetailActivityFormset # <-- Needed to get the empty_form template
)

# try:
#     from accounts.models import User 
# except ImportError:
#     # Fallback if User is imported directly via settings.AUTH_USER_MODEL in a different way
#     from django.contrib.auth import get_user_model
User = get_user_model()


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
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    """
    Displays the dashboard with plans based on the user's role and selected filter.
    """
    user_role = request.user.role.lower()
    # Updated prefetch to include the new activity structure for efficiency
    prefetch_fields = ('goals', 'kpis', 'major_activities__detail_activities') 
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
def plan_success(request, plan_id):
    return render(request, 'plans/plan_success.html', {'plan_id': plan_id})
    

@login_required
def view_plan(request, plan_id):
    """
    Displays the details of a specific plan with proper access control.
    """
    # Eagerly load all related data for efficient template rendering
    plan = get_object_or_404(
        Plan.objects.prefetch_related(
            'goals', 
            'kpis', 
            'major_activities__detail_activities' # Ensure activities are fetched
        ), 

        id=plan_id
    )
    
    user_role = request.user.role.lower()
    can_view = False

    # Access control logic based on user role and plan ownership
    if user_role == 'corporate' or (plan.user == request.user) or \
        (user_role == 'department' and plan.user.department == request.user.department):
        can_view = True
    
    if not can_view:
        raise Http404("You do not have permission to view this plan.")

    # Data is available via relationship managers
    # goals = plan.goals.all()
    # kpis = plan.kpis.all()
    # major_activities = plan.major_activities.all()
    
    context = {
        'plan': plan,
        'goals': plan.goals.all(),
        'kpis': plan.kpis.all(),
        'major_activities': plan.major_activities.all(), 
    }
    
    return render(request, 'plans/view_plan.html', context)
    

@login_required
def delete_plan(request, plan_id):
    plan_to_delete = get_object_or_404(Plan, pk=plan_id)
    if plan_to_delete.user != request.user:
        raise Http404("You do not have permission to delete this plan.")

    if request.method == 'POST':
        plan_to_delete.delete()
        return redirect('dashboard') 

    return redirect('dashboard')


# --- Core Activity Management Logic ---

def _get_detail_form_template():
    """Helper to generate the HTML template for new Detail Activities via JS."""
    # We use the factory class to get the empty_form
    # We use a placeholder prefix '-999' which JS will replace
    empty_detail_formset = DetailActivityFormset(prefix='detail_activities-999')
    detail_form_template_html = empty_detail_formset.empty_form.as_p()
    
    # Replace the formset index (0) and placeholder major index (999) with JS placeholders
    return detail_form_template_html.replace('detail_activities-999-0-', 'detail_activities-__MAJOR_INDEX__-__INDEX__-')


def _handle_nested_detail_activities(request, major_activity_instance, major_index):
    """
    Manually processes and saves Detail Activities data for a single Major Activity.
    
    Args:
        request: The HttpRequest object (containing POST data).
        major_activity_instance: The saved MajorActivity object.
        major_index: The form index of the Major Activity (e.g., '0', '1').
    """
    
    # The TOTAL_FORMS field is manually managed by JavaScript
    detail_total_forms_key = f'detail_activities-{major_index}-TOTAL_FORMS'
    try:
        total_details = int(request.POST.get(detail_total_forms_key, 0))
    except ValueError:
        total_details = 0 # Safety check

    for i in range(total_details):
        prefix = f'detail_activities-{major_index}-{i}'
        
        # Check for DELETE flag (set by JS for initial forms)
        delete_key = f'{prefix}-DELETE'
        if request.POST.get(delete_key) == 'on':
            # Check for PK to ensure we only delete existing items
            pk_key = f'{prefix}-id'
            detail_pk = request.POST.get(pk_key)
            if detail_pk:
                DetailActivity.objects.filter(pk=detail_pk).delete()
            continue

        # Check for PK to determine if this is an update (update existing instance) or create (no instance)
        pk_key = f'{prefix}-id'
        detail_pk = request.POST.get(pk_key)
        
        # Instantiate DetailActivityForm using the specific prefix for this form instance
        detail_form = DetailActivityForm(request.POST, 
                                         prefix=prefix, 
                                         instance=DetailActivity.objects.get(pk=detail_pk) if detail_pk else None)
        
        # Validation for individual detail form
        if detail_form.is_valid():
            detail_activity = detail_form.save(commit=False)
            detail_activity.major_activity = major_activity_instance
            detail_activity.save()
        elif detail_form.has_changed():
             # Re-raising validation errors here will cause the transaction to fail, 
             # which is desired to prevent partial saves.
             raise ValueError(f"Detail Activity Form {prefix} failed validation: {detail_form.errors}")
             
    # TODO: Add logic here to re-calculate and save MajorActivity.total_weight 
    # if you want to store it as a field instead of a property.

@login_required
def create_plan(request):

    #Uses transaction.atomic for all-or-nothing data saving.
    # Instantiate formsets for a POST request
    plan_type = request.POST.get('plan_type') or None
    formset_kwargs = {'plan_type': plan_type} if plan_type else {}
    
    # 1. Instantiate Formsets
    if request.method == 'POST':
        form = PlanCreationForm(request.POST)
        goal_formset = StrategicGoalFormset(request.POST, prefix='goals')
        kpi_formset = KPIFormset(request.POST, prefix='kpis', form_kwargs=formset_kwargs)
        major_activity_formset = MajorActivityFormset(request.POST, prefix='major_activities')
        
        # Check overall validity (Note: Detail Activities are NOT checked here, only on save)
        is_valid = form.is_valid() and goal_formset.is_valid() and kpi_formset.is_valid() and major_activity_formset.is_valid()
        
        if is_valid:
            try:
                with transaction.atomic():
                    # A. Save Plan Instance
                    plan = form.save(commit=False)
                    plan.user = request.user
                    plan.level = request.user.role.lower() # Assuming user role is the plan level
                    plan.save()
                    
                    # B. Save first-level inlines (Goals, KPIs)
                    goal_formset.instance = plan
                    goal_formset.save()
                    
                    kpi_formset.instance = plan
                    # Clear quarterly targets for non-yearly plans (existing logic)
                    if plan_type and plan_type != 'yearly':
                        for kpi_form in kpi_formset:
                            if not kpi_form.cleaned_data.get('DELETE', False) and kpi_form.cleaned_data.get('name'):
                                kpi_form.instance.target_q1 = 0.0
                                kpi_form.instance.target_q2 = 0.0
                                kpi_form.instance.target_q3 = 0.0
                                kpi_form.instance.target_q4 = 0.0
                    kpi_formset.save()
                    
                    # C. Save Major Activities and their nested Detail Activities
                    major_activities = major_activity_formset.save(commit=False)
                    
                    # Iterate through saved and unsaved major forms
                    for major_form in major_activity_formset:
                        if major_form.cleaned_data: # Only process forms with data
                            # Handle deletion first
                            if major_form.cleaned_data.get('DELETE', False):
                                if major_form.instance.pk:
                                    major_form.instance.delete()
                                continue
                            
                            # Save Major Activity
                            major_activity = major_form.save(commit=False)
                            major_activity.plan = plan
                            major_activity.save()
                            
                            # Manually process nested Detail Activities
                            major_index = major_form.prefix.split('-')[1] # Extracts '0', '1', etc.
                            _handle_nested_detail_activities(request, major_activity, major_index)
                            
                    return redirect('plan_success', plan_id=plan.id)
            
            except ValueError as ve:
                # Catch specific validation error from nested forms
                # Log the error and re-render the forms with the original POST data
                print(f"Nested Validation Failed: {ve}")
                # Optional: Add a general error message to the main form
                form.errors['__all__'] = 'A nested activity failed validation. Please check the details.'
            except Exception as e:
                # Catch general errors
                print(f"Transaction failed: {e}")
                form.errors['__all__'] = 'An unexpected error occurred during saving.'

        # If invalid or transaction failed, execution falls through to render the form with errors
        
    else:
        # GET request
        form = PlanCreationForm()
        goal_formset = StrategicGoalFormset(prefix='goals')
        kpi_formset = KPIFormset(prefix='kpis', form_kwargs=formset_kwargs)
        major_activity_formset = MajorActivityFormset(prefix='major_activities')

    context = {
        'form': form,
        'goal_formset': goal_formset,
        'kpi_formset': kpi_formset,
        'major_activity_formset': major_activity_formset,
        'plan_instance': None,
        # Pass the JavaScript template for Detail Activities
        'detail_form_template_html': _get_detail_form_template(),
    }
    return render(request, 'plans/create_plan.html', context)


@login_required
def edit_plan(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)
    if plan.user != request.user:
        raise Http404("You do not have permission to edit this plan.")

    # Determine plan_type for formset kwargs
    plan_type = request.POST.get('plan_type') or plan.plan_type
    formset_kwargs = {'plan_type': plan_type} if plan_type else {}

    # 1. Instantiate Formsets
    if request.method == 'POST':
        form = PlanCreationForm(request.POST, instance=plan)
        goal_formset = StrategicGoalFormset(request.POST, instance=plan, prefix='goals')
        kpi_formset = KPIFormset(request.POST, instance=plan, prefix='kpis', form_kwargs=formset_kwargs)
        major_activity_formset = MajorActivityFormset(request.POST, instance=plan, prefix='major_activities')

        is_valid = form.is_valid() and goal_formset.is_valid() and kpi_formset.is_valid() and major_activity_formset.is_valid()

        if is_valid:
            try:
                with transaction.atomic():
                    # A. Save Plan Instance
                    form.save()
                    
                    # B. Save first-level inlines (Goals, KPIs)
                    goal_formset.save()
                    
                    # Clear quarterly targets for non-yearly plans (existing logic)
                    if plan_type and plan_type != 'yearly':
                        for kpi_form in kpi_formset:
                            if not kpi_form.cleaned_data.get('DELETE', False) and kpi_form.cleaned_data.get('name'):
                                kpi_form.instance.target_q1 = 0.0
                                kpi_form.instance.target_q2 = 0.0
                                kpi_form.instance.target_q3 = 0.0
                                kpi_form.instance.target_q4 = 0.0
                    kpi_formset.save()
                    
                    # C. Save Major Activities and their nested Detail Activities
                    
                    # Iterate through saved and unsaved major forms (formset.save() handles DELETE flag for existing forms)
                    for major_form in major_activity_formset:
                        if major_form.cleaned_data: # Only process forms with data
                            # Handle deletion first (since save(commit=False) doesn't delete)
                            if major_form.cleaned_data.get('DELETE', False):
                                if major_form.instance.pk:
                                    major_form.instance.delete()
                                continue
                            
                            # Save Major Activity (update existing or save new)
                            major_activity = major_form.save(commit=False)
                            major_activity.plan = plan
                            major_activity.save()
                            
                            # Manually process nested Detail Activities
                            major_index = major_form.prefix.split('-')[1] # Extracts '0', '1', etc.
                            _handle_nested_detail_activities(request, major_activity, major_index)
                            
                    return redirect('dashboard')
            
            except ValueError as ve:
                # Catch specific validation error from nested forms
                print(f"Nested Validation Failed: {ve}")
                form.errors['__all__'] = 'A nested activity failed validation. Please check the details.'
            except Exception as e:
                # Catch general errors
                print(f"Transaction failed: {e}")
                form.errors['__all__'] = 'An unexpected error occurred during saving.'
                
        # If invalid or transaction failed, execution falls through to render the form with errors

    else:
        # GET request
        form = PlanCreationForm(instance=plan)
        goal_formset = StrategicGoalFormset(instance=plan, prefix='goals')
        kpi_formset = KPIFormset(instance=plan, prefix='kpis', form_kwargs=formset_kwargs) 
        major_activity_formset = MajorActivityFormset(instance=plan, prefix='major_activities')
        
    context = {
        'form': form,
        'goal_formset': goal_formset,
        'kpi_formset': kpi_formset,
        'major_activity_formset': major_activity_formset,
        'plan_instance': plan,
        # Pass the JavaScript template for Detail Activities
        'detail_form_template_html': _get_detail_form_template(),
    }
    return render(request, 'plans/create_plan.html', context)