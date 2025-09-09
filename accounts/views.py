from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import UserRegistrationForm     
from django.contrib.auth.views import LoginView

# Create your views here.

def role_select_view(request):
    return render(request, 'accounts/role_select.html')

def register_view(request):
    role = request.GET.get('role', 'individual')
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = role
            user.save()
            login(request, user)
            return redirect('plan_create')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form, 'role': role})
class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'

    def get_success_url(self):
        role = self.request.user.role
        return '/plan/create/'
        selected_role = request.POST.get('role')
        if selected_role:
            request.session['selected_role'] = selected_role
            return redirect('register')
