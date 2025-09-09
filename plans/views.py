from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse

# Import all plan models
from .models import WeeklyPlan, MonthlyPlan, QuarterlyPlan, YearlyPlan

# Weekly
from .weekly_plan_forms import (
    WeeklyPlanForm,
    WeeklyKPIFormSet,
    WeeklyGoalFormSet,
    WeeklyActivityFormSet
)

# Monthly
from .monthly_plan_form import (
    MonthlyPlanForm,
    KPIFormSet as MonthlyKPIFormSet,
    StrategicGoalFormSet as MonthlyGoalFormSet,
    ActivityFormSet as MonthlyActivityFormSet
)

# Quarterly
from .quarterly_plan_form import (
    QuarterlyPlanForm,
    KPIFormSet as QuarterlyKPIFormSet,
    StrategicGoalFormSet as QuarterlyGoalFormSet,
    ActivityFormSet as QuarterlyActivityFormSet
)

# Yearly
from .yearly_plan_form import (
    YearlyPlanForm,
    KPIFormSet as YearlyKPIFormSet,
    StrategicGoalFormSet as YearlyGoalFormSet,
    ActivityFormSet as YearlyActivityFormSet
)


@login_required
def select_plan_type_view(request):
    """User selects a plan type based on their role."""
    role = request.user.role.lower()

    allowed_levels_by_role = {
        'individual': [('weekly', 'Weekly'), ('monthly', 'Monthly')],
        'department': [('monthly', 'Monthly'), ('quarterly', 'Quarterly')],
        'corporate': [('quarterly', 'Quarterly'), ('yearly', 'Yearly')],
    }

    allowed_levels = allowed_levels_by_role.get(role, [])

    if request.method == 'POST':
        selected_level = request.POST.get('plan_level')
        return redirect(f"{reverse('create_plan')}?level={selected_level}")

    return render(request, 'plans/select_plan_type.html', {
        'allowed_levels': allowed_levels
    })


@login_required
def create_plan_view(request):
    """Render and save the correct plan form depending on the selected level."""
    level = request.GET.get('level')
    if not level:
        return redirect('select_plan_type')

    # Map levels to model/form/formset tuples
    plan_mapping = {
        'weekly': (WeeklyPlan, WeeklyPlanForm, WeeklyKPIFormSet, WeeklyGoalFormSet, WeeklyActivityFormSet),
        'monthly': (MonthlyPlan, MonthlyPlanForm, MonthlyKPIFormSet, MonthlyGoalFormSet, MonthlyActivityFormSet),
        'quarterly': (QuarterlyPlan, QuarterlyPlanForm, QuarterlyKPIFormSet, QuarterlyGoalFormSet, QuarterlyActivityFormSet),
        'yearly': (YearlyPlan, YearlyPlanForm, YearlyKPIFormSet, YearlyGoalFormSet, YearlyActivityFormSet),
    }

    if level not in plan_mapping:
        return redirect('select_plan_type')

    PlanModel, PlanFormClass, KPIFormSetClass, GoalFormSetClass, ActivityFormSetClass = plan_mapping[level]

    if request.method == 'POST':
        plan_form = PlanFormClass(request.POST)
        kpi_formset = KPIFormSetClass(request.POST)
        goal_formset = GoalFormSetClass(request.POST)
        activity_formset = ActivityFormSetClass(request.POST)

        if (plan_form.is_valid() and kpi_formset.is_valid() 
                and goal_formset.is_valid() and activity_formset.is_valid()):
            plan = plan_form.save(commit=False)
            plan.user = request.user
            plan.save()

            # Attach formsets to plan instance
            kpi_formset.instance = plan
            kpi_formset.save()

            goal_formset.instance = plan
            goal_formset.save()

            activity_formset.instance = plan
            activity_formset.save()

            return redirect('plan_list')
    else:
        plan_form = PlanFormClass()
        kpi_formset = KPIFormSetClass(queryset=PlanModel.kpis.none())
        goal_formset = GoalFormSetClass(queryset=PlanModel.goals.none())
        activity_formset = ActivityFormSetClass(queryset=PlanModel.activities.none())

    return render(request, 'plans/create_plan.html', {
        'plan_form': plan_form,
        'kpi_formset': kpi_formset,
        'goal_formset': goal_formset,
        'activity_formset': activity_formset,
        'level': level
    })


@login_required
def plan_list_view(request):
    """List all plans for the current user based on role."""
    role = request.user.role.lower()
    user = request.user
    selected_level = request.GET.get('level', None)

    plans = []

    if role == "corporate":
        plans = list(WeeklyPlan.objects.all()) + list(MonthlyPlan.objects.all()) + list(QuarterlyPlan.objects.all()) + list(YearlyPlan.objects.all())
    elif role == "department":
        plans = list(WeeklyPlan.objects.filter(user=user)) + list(MonthlyPlan.objects.filter(user=user)) + list(QuarterlyPlan.objects.filter(user=user))
    else:  # individual
        plans = list(WeeklyPlan.objects.filter(user=user)) + list(MonthlyPlan.objects.filter(user=user))

    # Filter by selected level
    if selected_level:
        level_map = {
            'weekly': WeeklyPlan,
            'monthly': MonthlyPlan,
            'quarterly': QuarterlyPlan,
            'yearly': YearlyPlan,
        }
        model_cls = level_map.get(selected_level)
        plans = [p for p in plans if isinstance(p, model_cls)]

    return render(request, 'plans/plan_list.html', {
        'plans': plans,
        'selected_level': selected_level,
        'user_role': role,
    })
