from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class UserRegistrationForm(UserCreationForm):
    """
    A custom form for user registration that includes the user's role and department,
    and correctly handles password creation.
    """
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('role', 'department',)
        
# The AuthenticationForm is not affected, but kept here for context.
class UserAuthenticationForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
