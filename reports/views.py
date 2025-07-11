from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Plan  
from .models import StrategicGoal
from .forms import PlanFilterForm  # Ensure this form is created  
from .forms import PlanForm  # Add this at the top with your imports
from django.shortcuts import redirect

from django.forms import inlineformset_factory
from .forms import StrategicGoalForm  # Make sure this is created
from .models.kpi import KPI, Target
from .forms import KPIForm, TargetForm
from django.forms import inlineformset_factory
from django.shortcuts import get_object_or_404


def home(request):
    return render(request, 'reports/home.html')

# Utility function to check role
def is_corporate(user):
    return user.groups.filter(name='Corporate').exists()

@login_required
@user_passes_test(is_corporate)
def corporate_dashboard(request):
    return render(request, 'reports/corporate_dashboard.html')



@login_required
def create_plan(request):
    if request.method == 'POST':
        form = PlanForm(request.POST)
        if form.is_valid():
            form.save(user=request.user)
            return redirect('view_plans')
    else:
        form = PlanForm()

    return render(request, 'reports/create_plan.html', {'form': form})

@login_required
def view_plans(request):
    user = request.user
    level = user.groups.first().name.upper() if user.groups.exists() else 'INDIVIDUAL'
    plans = Plan.objects.filter(user=user, level=level)
    return render(request, 'reports/view_plans.html', {'plans': plans})


@login_required
def view_goals(request, plan_id):
    plan = Plan.objects.get(id=plan_id, user=request.user)
    goals = plan.goals.all()  # uses related_name='goals'

    return render(request, 'reports/view_goals.html', {
        'plan': plan,
        'goals': goals,
    })


@login_required
def add_goals_to_plan(request, plan_id):
    plan = Plan.objects.get(id=plan_id, user=request.user)
    GoalFormSet = inlineformset_factory(Plan, StrategicGoal, form=StrategicGoalForm, extra=3, can_delete=False)

    if request.method == 'POST':
        formset = GoalFormSet(request.POST, instance=plan)
        if formset.is_valid():
            formset.save()
            return redirect('view_plans')
    else:
        formset = GoalFormSet(instance=plan)

    return render(request, 'reports/add_goals.html', {
        'formset': formset,
        'plan': plan
    })

@login_required
def view_plans(request):
    user = request.user
    level = user.groups.first().name.upper() if user.groups.exists() else 'INDIVIDUAL'
    plans = Plan.objects.filter(user=user, level=level)

    form = PlanFilterForm(request.GET or None)
    if form.is_valid():
        if form.cleaned_data.get('year'):
            plans = plans.filter(year=form.cleaned_data['year'])
        if form.cleaned_data.get('quarter'):
            plans = plans.filter(quarter__iexact=form.cleaned_data['quarter'])
        if form.cleaned_data.get('month'):
            plans = plans.filter(month__iexact=form.cleaned_data['month'])

    return render(request, 'reports/view_plans.html', {
        'plans': plans,
        'form': form
    })

@login_required
def add_kpis_to_goal(request, goal_id):
    goal = get_object_or_404(StrategicGoal, id=goal_id)
    KPIFormSet = inlineformset_factory(StrategicGoal, KPI, form=KPIForm, extra=2, can_delete=False)

    if request.method == 'POST':
        formset = KPIFormSet(request.POST, instance=goal)
        if formset.is_valid():
            kpis = formset.save()
            return redirect('view_goals', plan_id=goal.plan.id)
    else:
        formset = KPIFormSet(instance=goal)

    return render(request, 'reports/add_kpis.html', {
        'formset': formset,
        'goal': goal,
    })

@login_required
def add_targets_to_kpi(request, kpi_id):
    kpi = get_object_or_404(KPI, id=kpi_id)
    if request.method == 'POST':
        form = TargetForm(request.POST)
        if form.is_valid():
            target = form.save(commit=False)
            target.kpi = kpi
            target.save()
            return redirect('view_goals', plan_id=kpi.goal.plan.id)
    else:
        form = TargetForm()

    return render(request, 'reports/add_targets.html', {
        'form': form,
        'kpi': kpi
    })

