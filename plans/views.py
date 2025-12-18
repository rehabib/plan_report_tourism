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
    user = request.user
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
    elif user_role == 'strategic-team':
        plans = base_query.filter(
            Q(user=request.user) |
              Q(level__iexact='corporate') |
                Q(level__iexact='md')
        )

    elif user_role == 'md':
        plans = base_query.filter(
            Q(user=request.user) |
              Q(level__iexact='md') |
              Q(user__md=request.user)
        )   

    elif user_role == 'department':
        plans = base_query.filter(
            Q(user=request.user) | 
              Q(level__iexact='department', user__department__iexact=request.user.department)
 |
              Q(level__iexact='desk')|
              Q(level__iexact='individual', user__department=request.user.department)
        )

    elif user_role == 'desk':
          
                plans = base_query.filter(
                    Q(user=user) |
                    Q(level__iexact='desk', user__desk__iexact=request.user) |
                    Q(level__iexact='individual', user__desk__iexact=request.user.desk)
                )
            
    elif user_role == 'individual':
            plans = base_query.filter(user=user)
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
    goals = plan.goals.all()
    kpis = plan.kpis.all()
    major_activities = plan.major_activities.all()
    #goals = StrategicGoal.objects.filter(plan=plan)
    #kpis = KPI.objects.filter(plan=plan)
    #major_activities = MajorActivity.objects.filter(plan=plan)
    context = {
        'plan': plan,
        #'goals': goals,
        #'kpis': kpis,
        #'major_activities': major_activities,
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
    empty_detail_formset = DetailActivityFormset(prefix='detail_activities-999')
    detail_form_template_html = empty_detail_formset.empty_form.as_p()
    return detail_form_template_html.replace('detail_activities-999-0-', 'detail_activities-__MAJOR_INDEX__-__INDEX__-')


def _build_detail_formsets_for_plan(plan):
    """
    For each MajorActivity on a given plan, build a DetailActivityFormset
    with prefix detail_activities-{index} and return a dict mapping index->formset.
    """
    detail_formsets = {}
    for idx, major in enumerate(plan.major_activities.all()):
        prefix = f'detail_activities-{idx}'
        formset = DetailActivityFormset(instance=major, prefix=prefix)
        detail_formsets[str(idx)] = formset
    return detail_formsets


@login_required
def create_plan(request):
    plan_type = request.POST.get('plan_type') or None
    formset_kwargs = {'plan_type': plan_type} if plan_type else {}

    if request.method == 'POST':
        form = PlanCreationForm(request.POST)
        goal_formset = StrategicGoalFormset(request.POST, prefix='goal')
        kpi_formset = KPIFormset(request.POST, prefix='kpis', form_kwargs=formset_kwargs)
        major_activity_formset = MajorActivityFormset(request.POST, prefix='major_activities')

        is_valid = form.is_valid() and goal_formset.is_valid() and kpi_formset.is_valid() and major_activity_formset.is_valid()

        # We'll collect detail formsets for validation errors rendering
        detail_formsets_for_render = {}

        if is_valid:
            try:
                with transaction.atomic():
                    plan = form.save(commit=False)
                    plan.user = request.user
                    plan.level = request.user.role.lower()
                    plan.save()

                    goal_formset.instance = plan
                    goal_formset.save()

                    kpi_formset.instance = plan
                    if plan_type and plan_type != 'yearly':
                        for kpi_form in kpi_formset:
                            if not kpi_form.cleaned_data.get('DELETE', False) and kpi_form.cleaned_data.get('name'):
                                kpi_form.instance.target_q1 = 0.0
                                kpi_form.instance.target_q2 = 0.0
                                kpi_form.instance.target_q3 = 0.0
                                kpi_form.instance.target_q4 = 0.0
                    kpi_formset.save()

                    # Save Major Activities
                    major_forms = major_activity_formset.save(commit=False)

                    # We'll need to iterate through formset.forms (including existing) to respect prefixes/indexes
                    for major_index, major_form in enumerate(major_activity_formset):
                        # If formset provided cleaned_data
                        if not major_form.cleaned_data:
                            continue

                        # Handle delete
                        if major_form.cleaned_data.get('DELETE', False):
                            if major_form.instance.pk:
                                major_form.instance.delete()
                            continue

                        # Save or update major activity
                        major_activity = major_form.save(commit=False)
                        major_activity.plan = plan
                        major_activity.save()

                        # Build a DetailActivityFormset for this major using the prefix pattern
                        prefix = f'detail_activities-{major_index}'
                        # Create a formset instance bound to POST -> this will validate nested forms
                        detail_fs = DetailActivityFormset(request.POST, instance=major_activity, prefix=prefix)

                        detail_formsets_for_render[str(major_index)] = detail_fs

                        if detail_fs.is_valid():
                            # Save and set the major_activity foreign key is already handled by formset.save()
                            details = detail_fs.save(commit=False)
                            # Delete items flagged for deletion
                            for deleted in detail_fs.deleted_objects:
                                deleted.delete()
                            # Save or update details
                            for d in details:
                                d.major_activity = major_activity
                                d.save()

                            # After save, validate sum of detail weights equals major_form weight (if major has weight field as 'weight')
                            # In your models MajorActivity doesn't have a 'weight' field, so we check against total_weight property or you may want to compare to a field:
                            # If your MajorActivity had a numeric 'weight' field, uncomment the next block and change as needed.
                            # Example: if major_form has 'weight' field, use:
                            # major_weight = major_form.cleaned_data.get('weight')
                            # total_detail_weight = major_activity.total_weight
                            # if major_weight is not None and abs(float(total_detail_weight) - float(major_weight)) > 0.001:
                            #     raise ValueError(f"Sum of detail weights ({total_detail_weight}) does not equal Major Activity weight ({major_weight}).")

                        else:
                            # If detail_fs invalid -> raise to roll back and show errors
                            raise ValueError(f"Detail Activity formset for major index {major_index} failed validation: {detail_fs.errors}")

                    return redirect('plan_success', plan_id=plan.id)

            except ValueError as ve:
                print(f"Nested Validation Failed: {ve}")
                form.add_error(None, 'A nested activity failed validation. Please check the details.')
            except Exception as e:
                print(f"Transaction failed: {e}")
                form.add_error(None, 'An unexpected error occurred during saving.')

        # If invalid - prepare detail formsets for rendering (best effort)
        else:
            # Build detail formsets for existing majors so the template can render them with errors
            # Determine how many major forms we have in the POST (TOTAL_FORMS)
            try:
                major_total = int(request.POST.get('major_activities-TOTAL_FORMS', 0))
            except ValueError:
                major_total = 0

            for idx in range(major_total):
                prefix = f'detail_activities-{idx}'
                detail_formsets_for_render[str(idx)] = DetailActivityFormset(request.POST, prefix=prefix)

        # Fall through and render template with errors and detail_formsets_for_render
    else:
        form = PlanCreationForm()
        goal_formset = StrategicGoalFormset(prefix='goal')
        kpi_formset = KPIFormset(prefix='kpis', form_kwargs=formset_kwargs)
        major_activity_formset = MajorActivityFormset(prefix='major_activities')
        detail_formsets_for_render = {}  # empty on initial create

    context = {
        'form': form,
        'goal_formset': goal_formset,
        'kpi_formset': kpi_formset,
        'major_activity_formset': major_activity_formset,
        'plan_instance': None,
        'detail_form_template_html': _get_detail_form_template(),
        'detail_formsets': detail_formsets_for_render,
    }
    return render(request, 'plans/create_plan.html', context)


@login_required
def edit_plan(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)
    if plan.user != request.user:
        raise Http404("You do not have permission to edit this plan.")

    plan_type = request.POST.get('plan_type') or plan.plan_type
    formset_kwargs = {'plan_type': plan_type} if plan_type else {}

    detail_formsets_for_render = {}

    if request.method == 'POST':
        form = PlanCreationForm(request.POST, instance=plan)
        goal_formset = StrategicGoalFormset(request.POST, instance=plan, prefix='goal')
        kpi_formset = KPIFormset(request.POST, instance=plan, prefix='kpis', form_kwargs=formset_kwargs)
        major_activity_formset = MajorActivityFormset(request.POST, instance=plan, prefix='major_activities')

        is_valid = form.is_valid() and goal_formset.is_valid() and kpi_formset.is_valid() and major_activity_formset.is_valid()

        if is_valid:
            try:
                with transaction.atomic():
                    form.save()
                    goal_formset.save()

                    if plan_type and plan_type != 'yearly':
                        for kpi_form in kpi_formset:
                            if not kpi_form.cleaned_data.get('DELETE', False) and kpi_form.cleaned_data.get('name'):
                                kpi_form.instance.target_q1 = 0.0
                                kpi_form.instance.target_q2 = 0.0
                                kpi_form.instance.target_q3 = 0.0
                                kpi_form.instance.target_q4 = 0.0
                    kpi_formset.save()

                    # Save or update majors and nested details
                    for major_index, major_form in enumerate(major_activity_formset):
                        if not major_form.cleaned_data:
                            continue

                        if major_form.cleaned_data.get('DELETE', False):
                            if major_form.instance.pk:
                                major_form.instance.delete()
                            continue

                        major_activity = major_form.save(commit=False)
                        major_activity.plan = plan
                        major_activity.save()

                        prefix = f'detail_activities-{major_index}'
                        detail_fs = DetailActivityFormset(request.POST, instance=major_activity, prefix=prefix)
                        detail_formsets_for_render[str(major_index)] = detail_fs

                        if detail_fs.is_valid():
                            details = detail_fs.save(commit=False)
                            for deleted in detail_fs.deleted_objects:
                                deleted.delete()
                            for d in details:
                                d.major_activity = major_activity
                                d.save()
                        else:
                            raise ValueError(f"Detail Activity formset for major index {major_index} failed validation: {detail_fs.errors}")

                    return redirect('dashboard')

            except ValueError as ve:
                print(f"Nested Validation Failed: {ve}")
                form.add_error(None, 'A nested activity failed validation. Please check the details.')
            except Exception as e:
                print(f"Transaction failed: {e}")
                form.add_error(None, 'An unexpected error occurred during saving.')

        else:
            # build detail_formsets_for_render from POST so template can show them with errors
            try:
                major_total = int(request.POST.get('major_activities-TOTAL_FORMS', 0))
            except ValueError:
                major_total = 0

            for idx in range(major_total):
                prefix = f'detail_activities-{idx}'
                detail_formsets_for_render[str(idx)] = DetailActivityFormset(request.POST, prefix=prefix)

    else:
        # GET request: build initial formsets and nested detail formsets for existing majors
        form = PlanCreationForm(instance=plan)
        goal_formset = StrategicGoalFormset(instance=plan, prefix='goal')
        kpi_formset = KPIFormset(instance=plan, prefix='kpis', form_kwargs=formset_kwargs)
        major_activity_formset = MajorActivityFormset(instance=plan, prefix='major_activities')

        # Build detail formsets for each existing major activity and map to index
        for idx, major in enumerate(plan.major_activities.all()):
            prefix = f'detail_activities-{idx}'
            detail_formsets_for_render[str(idx)] = DetailActivityFormset(instance=major, prefix=prefix)

    context = {
        'form': form,
        'goal_formset': goal_formset,
        'kpi_formset': kpi_formset,
        'major_activity_formset': major_activity_formset,
        'plan_instance': plan,
        'detail_form_template_html': _get_detail_form_template(),
        'detail_formsets': detail_formsets_for_render,
    }
    return render(request, 'plans/create_plan.html', context)
