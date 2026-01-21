from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from .forms import UserRegistrationForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from plans.models import Plan, StrategicGoal, KPI, MajorActivity
from reports.models import Report


def register_view(request):
    """
    Handles user registration.
    GET: Displays the registration form.
    POST: Processes the form and creates a new user.
    """
    if request.user.is_authenticated:
        return redirect('dashboard') # Redirect if already logged in

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful. You are now logged in.", extra_tags="auth")
            return redirect('dashboard')  # Redirect to a home page or dashboard
        else:
            messages.error(request, "Unsuccessful registration. Invalid information.", extra_tags="auth")
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/auth.html', {'form': form, 'view_name': 'register'})

def login_view(request):
    """
    Handles user login.
    GET: Displays the login form.
    POST: Authenticates the user and logs them in.
    """
    if request.user.is_authenticated:
        return redirect('dashboard') # Redirect if already logged in

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"You are now logged in as {username}.", extra_tags="auth")
                return redirect('dashboard') # Redirect to a home page or dashboard
            else:
                messages.error(request, "Invalid username or password.", extra_tags="auth")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/auth.html', {'form': form, 'view_name': 'login'})

@login_required
def logout_view(request):
    """Logs out the current user."""
    if request.method == 'POST':
        logout(request)
        messages.info(request, "You have been logged out.", extra_tags="auth")
    return redirect('login')

@login_required
def dashboard(request):
    """
    Displays the user's dashboard with their plans and reports.
    
    This view now fetches all related goals, KPIs, and activities
    for the user's plans to support the dashboard template.
    """
    # Fetch all plans owned by the current user
    # Use prefetch_related to load related data efficiently
    plans = Plan.objects.filter(owner=request.user).prefetch_related(
        'goals__kpis'
    )

    # Fetch all reports submitted for the current user's plans
    reports = Report.objects.filter(plan__owner=request.user)

    context = {
        'plans': plans,
        'reports': reports,
    }
    return render(request, 'accounts/dashboard.html', context)
