import re
from django.template.loader import render_to_string
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
    DetailActivityFormset,
   
)

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


# def parse_detail_activities(post_data):
#     details = {}
#     for key, value in post_data.items():
#         if not key.startswith("detail_activities-"):
#             continue
#         parts = key.split("-")
#         if len(parts) < 4:
#             continue
#         _, major_idx, detail_idx, field = parts[0], parts[1], parts[2], "-".join(parts[3:])
#         details.setdefault(major_idx, {})
#         details[major_idx].setdefault(detail_idx, {})
#         details[major_idx][detail_idx][field] = value
#     return details

def parse_detail_activities(post_data):
    """
    Extracts detail activity data from POST payload.
    Supports unlimited dynamic detail activities.
    """
    details = {}

    for key, value in post_data.items():
        if not key.startswith("detail_activities-"):
            continue

        # Expected format:
        # detail_activities-<major_index>-<detail_index>-<field_name>
        parts = key.split("-")
        if len(parts) < 4:
            continue

        major_idx = parts[1]
        detail_idx = parts[2]
        field = "-".join(parts[3:])  # handles fields with hyphens

        details.setdefault(major_idx, {})
        details[major_idx].setdefault(detail_idx, {})
        details[major_idx][detail_idx][field] = value

    return details


@login_required
def create_plan(request):
    plan_type = request.POST.get('plan_type') or None
    formset_kwargs = {'plan_type': plan_type} if plan_type else {}

    if request.method == 'POST':
        form = PlanCreationForm(request.POST)
        goal_formset = StrategicGoalFormset(request.POST, prefix='goal')
        kpi_formset = KPIFormset(request.POST, prefix='kpis', form_kwargs=formset_kwargs)
        major_formset = MajorActivityFormset(request.POST, prefix='major_activities')

        if form.is_valid() and goal_formset.is_valid() and kpi_formset.is_valid() and major_formset.is_valid():
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
                            if not kpi_form.cleaned_data.get('DELETE') and kpi_form.cleaned_data.get('name'):
                                kpi_form.instance.target_q1 = 0
                                kpi_form.instance.target_q2 = 0
                                kpi_form.instance.target_q3 = 0
                                kpi_form.instance.target_q4 = 0
                    kpi_formset.save()

                    # ===== SAVE MAJOR ACTIVITIES CORRECTLY =====
                major_formset.instance = plan
                major_formset.save()

                detail_map = parse_detail_activities(request.POST)

                # Loop through major_formset instead of enumerating DB results
                for major_index, major_form in enumerate(major_formset.forms):
                    if major_form.cleaned_data.get('DELETE'):
                        continue
                    
                    major = major_form.instance
                    
                    # Clear old details in edit mode
                    DetailActivity.objects.filter(major_activity=major).delete()

                    # Get detail activities for this major
                    for fields in detail_map.get(str(major_index), {}).values():

                        if fields.get('DELETE') in ('on', '1', 'true'):
                            continue

                        if not fields.get('detail_activity'):
                            continue

                        user_id = fields.get('responsible_person')
                        responsible_user = User.objects.filter(id=user_id).first() if user_id else None

                        DetailActivity.objects.create(
                            major_activity=major,
                            detail_activity=fields.get('detail_activity'),
                            weight=fields.get('weight') or 0,
                            responsible_person=responsible_user,
                            status=fields.get('status', 'PENDING')
                        )



                return redirect('plan_success', plan_id=plan.id)
            except Exception as e:
                print(e)
                form.add_error(None, 'An error occurred while saving the plan.')

    else:
        form = PlanCreationForm()
        goal_formset = StrategicGoalFormset(prefix='goal')
        kpi_formset = KPIFormset(prefix='kpis', form_kwargs=formset_kwargs)
        major_formset = MajorActivityFormset(prefix='major_activities')
    # ===== EMPTY DETAIL ACTIVITY FORM (for JS cloning) =====
        empty_detail_formset = DetailActivityFormset(
            prefix='detail_activities-__MAJOR_INDEX__'
        )

        detail_form_template_html = render_to_string(
            'plans/partials/detail_activity_form.html',
            {
                'detail_form': empty_detail_formset.empty_form,
                'major_index': '__MAJOR_INDEX__',
                'detail_index': '__INDEX__',
            }
        )
    return render(request, 'plans/create_plan.html', {
        'form': form,
        'goal_formset': goal_formset,
        'kpi_formset': kpi_formset,
        'major_activity_formset': major_formset,
        'detail_formsets': {},
        'detail_form_template_html': detail_form_template_html,
    })


@login_required
def edit_plan(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)
    if plan.user != request.user:
        raise Http404

    plan_type = request.POST.get('plan_type') or plan.plan_type
    formset_kwargs = {'plan_type': plan_type} if plan_type else {}

    if request.method == 'POST':
        form = PlanCreationForm(request.POST, instance=plan)
        goal_formset = StrategicGoalFormset(request.POST, instance=plan, prefix='goal')
        kpi_formset = KPIFormset(request.POST, instance=plan, prefix='kpis', form_kwargs=formset_kwargs)
        major_formset = MajorActivityFormset(request.POST, instance=plan, prefix='major_activities')

        if form.is_valid() and goal_formset.is_valid() and kpi_formset.is_valid() and major_formset.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                    goal_formset.save()

                    if plan_type and plan_type != 'yearly':
                        for kpi_form in kpi_formset:
                            if not kpi_form.cleaned_data.get('DELETE'):
                                kpi_form.instance.target_q1 = 0
                                kpi_form.instance.target_q2 = 0
                                kpi_form.instance.target_q3 = 0
                                kpi_form.instance.target_q4 = 0
                    kpi_formset.save()

                    # ===== SAVE MAJOR ACTIVITIES CORRECTLY =====
                    major_formset.instance = plan
                    major_formset.save()

                    # ===== SAVE DETAIL ACTIVITIES (OPTION A) =====
                    detail_map = parse_detail_activities(request.POST)
                    for major_index, major in enumerate(plan.major_activities.all()):
                        DetailActivity.objects.filter(major_activity=major).delete()
                        for fields in detail_map.get(str(major_index), {}).values():
                            if fields.get('DELETE') in ('on', '1', 'true'):
                                continue
                            if not fields.get('detail_activity'):
                                continue
                            DetailActivity.objects.create(
                                major_activity=major,
                                detail_activity=fields.get('detail_activity'),
                                weight=fields.get('weight') or 0,
                                responsible_person=fields.get('responsible_person'),
                            )

                    return redirect('dashboard')
            except Exception as e:
                print(e)
                form.add_error(None, 'Error updating plan.')

    else:
        form = PlanCreationForm(instance=plan)
        goal_formset = StrategicGoalFormset(instance=plan, prefix='goal')
        kpi_formset = KPIFormset(instance=plan, prefix='kpis', form_kwargs=formset_kwargs)
        major_formset = MajorActivityFormset(instance=plan, prefix='major_activities')
    # ===== EMPTY DETAIL ACTIVITY FORM (for JS cloning) =====
        empty_detail_formset = DetailActivityFormset(
            prefix='detail_activities-__MAJOR_INDEX__'
        )

        detail_form_template_html = render_to_string(
            'plans/partials/detail_activity_form.html',
            {
                'detail_form': empty_detail_formset.empty_form,
                'major_index': '__MAJOR_INDEX__',
                'detail_index': '__INDEX__',
            }
        )
    return render(request, 'plans/create_plan.html', {
        'form': form,
        'goal_formset': goal_formset,
        'kpi_formset': kpi_formset,
        'major_activity_formset': major_formset,
        'detail_formsets': {},
        'detail_form_template_html': detail_form_template_html,
        'plan_instance': plan,
    })