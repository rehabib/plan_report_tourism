import re
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
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
    DetailActivityFormset # The DetailActivityFormset factory class is needed
)
# Assuming 'accounts' is the app name where User model is defined/aliased
try:
    from accounts.models import User 
except ImportError:
    # Fallback if User is imported directly via settings.AUTH_USER_MODEL in a different way
    from django.contrib.auth import get_user_model
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


# Helper function to process nested MajorActivity/DetailActivity formsets
def process_activity_formsets(request, plan, major_activity_formset):
    """
    Handles validation and saving of MajorActivityFormset and its nested DetailActivityFormsets.
    
    CRITICAL: This iterates over the MajorActivity forms, saves the MajorActivity 
    instance (to get a PK), and then instantiates and validates the nested 
    DetailActivityFormset using a dynamic prefix linked to the parent form.
    
    Returns True on success, or False if any formset fails validation.
    """
    
    # 1. First-level save (MajorActivity) - Get instances without saving to DB yet
    # We use save(commit=False) to ensure we have instances to iterate over, 
    # even though we save them individually later to get their PKs.
    major_activities_instances = major_activity_formset.save(commit=False)
    
    # Track which MajorActivities are new and need to be saved to the database.
    new_major_activity_pks = []

    for i, major_activity_form in enumerate(major_activity_formset.forms):
        
        # Determine the MajorActivity instance (existing or new)
        major_activity = major_activity_form.instance
        
        # If the form is marked for deletion, handle it and skip
        if major_activity_form.cleaned_data.get('DELETE'):
            if major_activity.pk:
                major_activity.delete()
            continue
            
        # If the form is completely empty (extra form not filled), skip
        if not major_activity_form.has_changed() and not major_activity.pk and not major_activity_form.cleaned_data:
             continue
        
        # Ensure MajorActivity instance is saved before processing nested formset
        # We MUST save here to get a primary key (PK) for the child formset to link to
        is_new = not major_activity.pk
        if is_new:
            major_activity.plan = plan
            major_activity.save()
            new_major_activity_pks.append(major_activity.pk)

        # 2. Second-level instantiation and validation (DetailActivity)
        # The prefix must uniquely link the child formset to its parent form in the POST data
        # We use the parent form's prefix to ensure uniqueness: f'detail_activities-major_activities-0'
        detail_activity_formset = DetailActivityFormset(
            request.POST, 
            request.FILES, 
            instance=major_activity,
            prefix=f'detail_activities-{major_activity_form.prefix}'
        )

        if not detail_activity_formset.is_valid():
            # If validation fails, revert the changes if it was a new major activity
            if is_new:
                 major_activity.delete() # Transaction will roll back, but delete the unsaved instance reference

            # Add errors from nested formset back to the parent form to display them
            for detail_form in detail_activity_formset.forms:
                if detail_form.errors:
                    # Collect all errors from the detail form and display them on the parent form
                    error_messages = ", ".join([f"{k}: {v[0]}" for k, v in detail_form.errors.items()])
                    major_activity_form.add_error(None, f"Errors in Detail Activities for '{major_activity.name or 'New Activity'}': {error_messages}")
            return False # Validation failed

        # 3. Save DetailActivity formset
        # Save the MajorActivity instance again in case it was an existing instance that was updated
        major_activity_form.save() 
        detail_activity_formset.save()
            
    # Handle forms that were marked for deletion (MajorActivities that existed previously)
    major_activity_formset.save_m2m() # No m2m fields but good practice if added later

    return True


@login_required
def create_plan(request):
    """
    Handles the creation of a new plan with nested goals, KPIs, and activities.
    Uses transaction.atomic for all-or-nothing data saving.
    """
    # Instantiate formsets for a POST request
    if request.method == 'POST':
        form = PlanCreationForm(request.POST)

        # 1. Determine plan_type for formset kwargs
        posted_plan_type = request.POST.get('plan_type')
        plan_type = None
        formset_kwargs = {}

        if form.is_valid():
            plan_type = form.cleaned_data.get('plan_type')
        elif posted_plan_type:
            plan_type = posted_plan_type
            
        if plan_type:
            formset_kwargs = {'plan_type': plan_type}
        
        # 2. Instantiate formsets with POST data
        goal_formset = StrategicGoalFormset(request.POST, prefix='goals')
        kpi_formset = KPIFormset(request.POST, prefix='kpis', form_kwargs=formset_kwargs)
        major_activity_formset = MajorActivityFormset(request.POST, prefix='major_activities')

        # Use an outer flag to check for overall validity before entering the transaction
        is_valid = form.is_valid() and goal_formset.is_valid() and kpi_formset.is_valid() and major_activity_formset.is_valid()

        if is_valid:
            try:
                with transaction.atomic():
                    
                    # A. Prepare & Save Plan Instance
                    plan = form.save(commit=False)
                    plan.user = request.user
                    plan.level = request.user.role.lower()
                    plan.save()
                    
                    # B. Save first-level inlines (Goals, KPIs)
                    goal_formset.instance = plan
                    goal_formset.save()
                    
                    kpi_formset.instance = plan
                    
                    # Clear quarterly targets for non-yearly plans before saving KPIs
                    if plan_type and plan_type != 'yearly':
                        for kpi_form in kpi_formset:
                            # Check if the form has data and is not marked for deletion
                            if kpi_form.has_changed() or kpi_form.instance.pk:
                                if not kpi_form.cleaned_data.get('DELETE', False) and kpi_form.cleaned_data.get('name'):
                                    kpi_form.instance.target_q1 = 0.0
                                    kpi_form.instance.target_q2 = 0.0
                                    kpi_form.instance.target_q3 = 0.0
                                    kpi_form.instance.target_q4 = 0.0

                    kpi_formset.save()
                    
                    # C. Handle nested activities (will save major and detail activities)
                    if not process_activity_formsets(request, plan, major_activity_formset):
                        # If validation in process_activity_formsets fails, errors are added to the formset, 
                        # and we raise an exception to trigger the rollback of the transaction.
                        # The error has already been added to the relevant MajorActivityForm.
                        raise Exception("Nested activity validation failed, transaction rolled back.")


                return redirect('plan_success', plan_id=plan.id)
            
            except Exception as e:
                # The transaction rolls back due to the raised exception. 
                # We simply fall through to render the form with the errors present on the formsets.
                print(f"Transaction failed: {e}")
                pass

        # If form or formsets are invalid, they fall through to here with errors
        
    else:
        # GET request
        form = PlanCreationForm()
        goal_formset = StrategicGoalFormset(prefix='goals')
        kpi_formset = KPIFormset(prefix='kpis')
        major_activity_formset = MajorActivityFormset(prefix='major_activities')

    context = {
        'form': form,
        'goal_formset': goal_formset,
        'kpi_formset': kpi_formset,
        'major_activity_formset': major_activity_formset,
        'detail_activity_formset': DetailActivityFormset, # Pass the class for dynamic rendering in template
        'plan_instance': None,
    }
    return render(request, 'plans/create_plan.html', context)


@login_required
def edit_plan(request, plan_id):
    """
    Handles the editing of an existing plan and its related goals, KPIs, and nested activities.
    """
    plan = get_object_or_404(Plan, id=plan_id)
    
    # Check permissions
    if plan.user != request.user:
        raise Http404("You do not have permission to edit this plan.")

    # Instantiate formsets for a POST request
    if request.method == 'POST':
        form = PlanCreationForm(request.POST, instance=plan)
        
        # 1. Determine plan_type based on POST data or existing instance
        posted_plan_type = request.POST.get('plan_type')
        plan_type = None
        
        if form.is_valid():
            plan_type = form.cleaned_data.get('plan_type')
        elif posted_plan_type:
            plan_type = posted_plan_type
        else:
            plan_type = plan.plan_type
            
        formset_kwargs = {'plan_type': plan_type} if plan_type else {}

        # 2. Instantiate formsets with POST data and instance
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
                    
                    # Clear quarterly targets for non-yearly plans before saving KPIs
                    if plan_type and plan_type != 'yearly':
                        for kpi_form in kpi_formset:
                            # Check if the form has data and is not marked for deletion
                            if kpi_form.has_changed() or kpi_form.instance.pk:
                                if not kpi_form.cleaned_data.get('DELETE', False) and kpi_form.cleaned_data.get('name'):
                                    kpi_form.instance.target_q1 = 0.0
                                    kpi_form.instance.target_q2 = 0.0
                                    kpi_form.instance.target_q3 = 0.0
                                    kpi_form.instance.target_q4 = 0.0
                                    
                    kpi_formset.save()
                    
                    # C. Handle nested activities (will save major and detail activities)
                    if not process_activity_formsets(request, plan, major_activity_formset):
                        # Validation failed within the helper function. Rollback initiated by exception.
                        raise Exception("Nested activity validation failed, transaction rolled back.")

                return redirect('dashboard')
            
            except Exception as e:
                # Catch error from failed nested save and re-render forms with errors
                print(f"Transaction failed: {e}")
                pass

    else:
        # GET request
        form = PlanCreationForm(instance=plan)
        
        plan_type = plan.plan_type
        formset_kwargs = {'plan_type': plan_type} if plan_type else {}

        # 2. Instantiate formsets with existing instance and plan_type
        goal_formset = StrategicGoalFormset(instance=plan, prefix='goals')
        kpi_formset = KPIFormset(instance=plan, prefix='kpis', form_kwargs=formset_kwargs)
        major_activity_formset = MajorActivityFormset(instance=plan, prefix='major_activities')

    context = {
        'form': form,
        'goal_formset': goal_formset,
        'kpi_formset': kpi_formset,
        'major_activity_formset': major_activity_formset, 
        'detail_activity_formset': DetailActivityFormset, # Pass the class for dynamic rendering in template
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
    # Eagerly load all related data for efficient template rendering
    plan = get_object_or_404(
        Plan.objects.prefetch_related(
            'goals', 
            'kpis', 
            'major_activities__detail_activities' # Prefetch all nested data
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
    goals = plan.goals.all()
    kpis = plan.kpis.all()
    major_activities = plan.major_activities.all()
    
    context = {
        'plan': plan,
        'goals': goals,
        'kpis': kpis,
        # Pass Major Activities to the template for nested display 
        'major_activities': major_activities, 
    }
    
    return render(request, 'plans/view_plan.html', context)
    

@login_required
def delete_plan(request, plan_id):
    """
    Deletes a specific plan (only accessible by the plan creator).
    """
    plan_to_delete = get_object_or_404(Plan, pk=plan_id)
    
    # Simple check for ownership before deletion
    if plan_to_delete.user != request.user:
        raise Http404("You do not have permission to delete this plan.")

    if request.method == 'POST':
        plan_to_delete.delete()
        return redirect('dashboard') 

    return redirect('dashboard')