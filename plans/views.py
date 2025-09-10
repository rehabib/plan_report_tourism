from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q
from .models import Plan, StrategicGoal, KPI, Activity
from .forms import PlanCreationForm

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
    return render(request, 'plans/login.html', {'form': form})

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
    Displays the dashboard with plans based on the user's role.
    """
    user_role = request.user.role.lower()
    plans = Plan.objects.none()

    if user_role == 'corporate':
        # Corporate users can see all plans
        plans = Plan.objects.all().order_by('-year', '-month', '-week_number')
    elif user_role == 'department':
        # Department users can see their own plans and all individual plans
        plans = Plan.objects.filter(Q(user=request.user) | Q(level='individual')).order_by('-year', '-month', '-week_number')
    elif user_role == 'individual':
        # Individual users can only see their own plans
        plans = Plan.objects.filter(user=request.user).order_by('-year', '-month', '-week_number')

    context = {
        'user_role': user_role,
        'plans': plans
    }
    return render(request, 'plans/dashboard.html', context)

@login_required
def create_plan(request):
    """
    Handles the creation of a new plan and its related goals, KPIs, and activities.
    """
    if request.method == 'POST':
        form = PlanCreationForm(request.POST)
        if form.is_valid():
            # Create the main Plan object
            plan = form.save(commit=False)
            plan.user = request.user
            plan.level = request.user.role.lower() # Set the plan level based on the user's role
            plan.save()

            # Create related models
            goal = StrategicGoal.objects.create(plan=plan, title=form.cleaned_data['goal_title'])
            kpi = KPI.objects.create(
                plan=plan,
                name=form.cleaned_data['kpi_name'],
                baseline=form.cleaned_data['kpi_baseline'],
                target=form.cleaned_data['kpi_target']
            )
            Activity.objects.create(
                plan=plan,
                goal=goal,
                major_activity=form.cleaned_data['major_activity'],
                detail_activity=form.cleaned_data['detail_activity'],
                responsible_person=form.cleaned_data['responsible_person'],
                budget=form.cleaned_data['budget']
            )
            return redirect('dashboard')
    else:
        form = PlanCreationForm()

    context = {
        'form': form,
    }
    return render(request, 'plans/create_plan.html', context)
