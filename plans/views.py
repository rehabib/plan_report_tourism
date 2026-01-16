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
from .models import Department, Plan, StrategicGoal, KPI, MajorActivity, DetailActivity
from .forms import (
    PlanCreationForm, 
    StrategicGoalFormset, 
    KPIFormset, 
    MajorActivityFormset, 
    DetailActivityFormset,
    PlanCreationForm,
    StrategicGoalForm,
    KPIForm,
    MajorActivityForm,
    DetailActivityForm,
    BaseDetailActivityFormSet
   
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
    Dashboard shows all plans the user is allowed to see:
    - Own plans
    - Plans waiting for user's approval
    - Plans in user's organizational scope
    """

    user = request.user
    user_role = user.role.lower()

    base_queryset = (
        Plan.objects
        .select_related("user")
        .prefetch_related(
            "goals",
            "kpis",
            "major_activities__detail_activities",
        )
        .order_by("-created_at")
    )

    show_my_plans = request.GET.get("show") == "my_plans"
    selected_department = request.GET.get("department")

    visibility = Q(user=user)  # 1️⃣ Own plans always visible

    # 2️⃣ Plans waiting for user's approval
    visibility |= Q(current_reviewer_role=user_role)

    # Desk → Individual in same department
    if user_role == "desk" and user.department:
        visibility |= Q(level="individual", user__department=user.department)

    # Department → Desk + Individual in same department
    if user_role == "department" and user.department:
        visibility |= Q(level__in=["desk","individual"], user__department=user.department)

    # 4️⃣ Pillar heads see all plans in their pillar
    if user_role in [
        "corporate",
        "state-minister-destination",
        "state-minister-promotion",
    ]:
        visibility |= Q(pillar=user.pillar)

    # 5️⃣ Strategic team sees submitted pillar plans
    if user_role == "strategic-team":
            visibility |= Q(level__in=["corporate","state-minister-destination","state-minister-promotion"],
                            status="SUBMITTED",
                            current_reviewer_role="strategic-team")
    # 6️⃣ Minister sees plans approved by strategic team
    if user_role == "minister":
         visibility |= Q(level="strategic-team",
            current_reviewer_role="minister"
        )

    plans = base_queryset.filter(visibility).distinct()

    # ----------------------------
    # FILTER: My Plans Only
    # ----------------------------
    if show_my_plans:
        plans = plans.filter(user=user)

    # ----------------------------
    # FILTER: Department (Corporate only)
    # ----------------------------
    # Department filter for pillar heads (Corporate + State Ministers)
    all_departments = []
    if user_role in ["corporate", "state-minister-destination", "state-minister-promotion"]:
        all_departments = (
            Department.objects
            .filter.filter(pillar__iexact=user_role)
        .values_list("name", flat=True)
    )

        if selected_department:
            plans = plans.filter(user__department__name__iexact=selected_department)


    return render(request, "plans/dashboard.html", {
        "plans": plans,
        "user_role": user_role,
        "show_my_plans": show_my_plans,
        "all_departments": all_departments,
        "selected_department": selected_department,
    })


# @login_required
# def dashboard(request):
#     """
#     Displays the dashboard with plans based on the user's role and selected filter.
#     """
#     user_role = request.user.role.lower()
#     user = request.user
#     # Updated prefetch to include the new activity structure for efficiency
#     prefetch_fields = ('goals', 'kpis', 'major_activities__detail_activities') 
#     base_query = Plan.objects.all().prefetch_related(*prefetch_fields).order_by('-year', '-month', '-week_number')

#     show_my_plans = request.GET.get('show', 'all') == 'my_plans'
#     selected_department_name = request.GET.get('department', '')

#     if show_my_plans:
#         plans = base_query.filter(user=request.user)

#     elif user_role == 'corporate':
#         if selected_department_name:
#             plans = base_query.filter(user__department__iexact=selected_department_name)
#         else:
#             plans = base_query
#     elif user_role == 'strategic-team':
#         plans = base_query.filter(
#             Q(user=request.user) |
#               Q(level__iexact='corporate') |
#                 Q(level__iexact='md')
#         )

#     elif user_role == 'md':
#         plans = base_query.filter(
#             Q(user=request.user) |
#               Q(level__iexact='md') |
#               Q(user__md=request.user)
#         )   

#     elif user_role == 'department':
#         plans = base_query.filter(
#             Q(user=request.user) | 
#               Q(level__iexact='department', user__department__iexact=request.user.department)
#  |
#               Q(level__iexact='desk')|
#               Q(level__iexact='individual', user__department=request.user.department)
#         )

#     elif user_role == 'desk':
          
#                 plans = base_query.filter(
#                     Q(user=user) |
#                     Q(level__iexact='desk', user__desk__iexact=request.user) |
#                     Q(level__iexact='individual', user__desk__iexact=request.user.desk)
#                 )
            
#     elif user_role == 'individual':
#             plans = base_query.filter(user=user)
#     else:
#         plans = Plan.objects.none() # Default safety

#     all_departments = []
#     if user_role == 'corporate':
#         all_departments = User.objects.filter(department__isnull=False).values_list('department', flat=True).distinct()

#     context = {
#         'user_role': user_role,
#         'plans': plans,
#         'show_my_plans': show_my_plans,
#         'all_departments': all_departments,
#         'selected_department': selected_department_name,
#     }
#     return render(request, 'plans/dashboard.html', context)

@login_required
def plan_success(request, plan_id):
    return render(request, 'plans/plan_success.html', {'plan_id': plan_id})
    

@login_required
def view_plan(request, plan_id):
    """
    Displays the details of a specific plan with proper access control.
    """
    # Eagerly load related objects for efficiency
    plan = get_object_or_404(
        Plan.objects.prefetch_related(
            "goals",
            "kpis",
            "major_activities__detail_activities",
        ),
        id=plan_id
    )

    user = request.user

    # Use the centralized can_user_view method
    if not plan.can_user_view(user):
        raise Http404("You do not have permission to view this plan.")

    context = {
        "plan": plan,
        "goals": plan.goals.all(),
        "kpis": plan.kpis.all(),
        "major_activities": plan.major_activities.all(),
    }

    return render(request, "plans/view_plan.html", context)

    

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

    # ---------- FORMSETS ----------
    StrategicGoalFormsetEdit = inlineformset_factory(
        Plan, StrategicGoal,
        form=StrategicGoalForm,
        extra=0,
        can_delete=True
    )

    KPIFormsetEdit = inlineformset_factory(
        Plan, KPI,
        form=KPIForm,
        extra=0,
        can_delete=True
    )

    MajorActivityFormsetEdit = inlineformset_factory(
        Plan, MajorActivity,
        form=MajorActivityForm,
        extra=0,
        can_delete=True
    )

    DetailActivityFormsetEdit = inlineformset_factory(
        MajorActivity, DetailActivity,
        form=DetailActivityForm,
        formset=BaseDetailActivityFormSet,
        extra=0,
        can_delete=True
    )

    # ---------- POST ----------
    if request.method == 'POST':
        form = PlanCreationForm(request.POST, instance=plan)
        goal_formset = StrategicGoalFormsetEdit(request.POST, instance=plan, prefix='goal')
        kpi_formset = KPIFormsetEdit(
            request.POST,
            instance=plan,
            prefix='kpis',
            form_kwargs=formset_kwargs
        )
        major_formset = MajorActivityFormsetEdit(
            request.POST,
            instance=plan,
            prefix='major_activities'
        )

      

        if (
            form.is_valid()
            and goal_formset.is_valid()
            and kpi_formset.is_valid()
            and major_formset.is_valid()
        ):
            try:
                with transaction.atomic():
                    # ----- SAVE PLAN -----
                    form.save()

                    # ----- SAVE GOALS -----
                    goal_formset.save()

                    # ----- SAVE KPIs -----
                    if plan_type and plan_type != 'yearly':
                        for kpi_form in kpi_formset:
                            if not kpi_form.cleaned_data.get('DELETE'):
                                kpi_form.instance.target_q1 = 0
                                kpi_form.instance.target_q2 = 0
                                kpi_form.instance.target_q3 = 0
                                kpi_form.instance.target_q4 = 0
                    kpi_formset.save()

                    # ----- SAVE MAJOR ACTIVITIES -----
                    major_formset.save()

                    # ----- SAVE DETAIL ACTIVITIES (NESTED) -----
                    detail_map = parse_detail_activities(request.POST)

                    for major_index, major_form in enumerate(major_formset.forms):
                        if major_form.cleaned_data.get('DELETE'):
                            continue

                        major = major_form.instance

                        # Clear existing details (edit-safe)
                        DetailActivity.objects.filter(
                            major_activity=major
                        ).delete()

                        for fields in detail_map.get(str(major_index), {}).values():
                            if fields.get('DELETE') in ('on', '1', 'true'):
                                continue

                            if not fields.get('detail_activity'):
                                continue

                            user_id = fields.get('responsible_person')
                            responsible_user = (
                                User.objects.filter(id=user_id).first()
                                if user_id else None
                            )

                            DetailActivity.objects.create(
                                major_activity=major,
                                detail_activity=fields.get('detail_activity'),
                                weight=fields.get('weight') or 0,
                                responsible_person=responsible_user,
                                status=fields.get('status', 'PENDING')
                            )

                return redirect('dashboard')

            except Exception as e:
                print(e)
                form.add_error(None, 'Error updating plan.')

    # ---------- GET ----------
    else:
        form = PlanCreationForm(instance=plan)
        goal_formset = StrategicGoalFormsetEdit(instance=plan, prefix='goal')
        kpi_formset = KPIFormsetEdit(
            instance=plan,
            prefix='kpis',
            form_kwargs=formset_kwargs
        )
        major_formset = MajorActivityFormsetEdit(
            instance=plan,
            prefix='major_activities'
        )
# LOAD DETAIL ACTIVITIES PER MAJOR ACTIVITY
        detail_formsets = {}
        for idx, major_form in enumerate(major_formset.forms):
            major_instance = major_form.instance
            detail_formsets[str(idx)] = DetailActivityFormsetEdit(
                instance=major_instance,
                prefix=f'detail_activities-{idx}'
            )
    # ---------- EMPTY DETAIL FORM (JS TEMPLATE) ----------
    empty_detail_formset = DetailActivityFormsetEdit(
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

    return render(request, 'plans/edit_plan.html', {
        'form': form,
        'goal_formset': goal_formset,
        'kpi_formset': kpi_formset,
        'major_activity_formset': major_formset,
        'detail_formsets': detail_formsets,
        'detail_form_template_html': detail_form_template_html,
        'plan_instance': plan,
    })

@login_required
def submit_plan(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)

    # Only owner can submit
    if plan.user != request.user:
        raise Http404("You do not have permission to submit this plan.")

    # Only draft plans can be submitted
    if plan.status == "PENDING":
        plan.status = "SUBMITTED"
        plan.save()

    return redirect("dashboard")

