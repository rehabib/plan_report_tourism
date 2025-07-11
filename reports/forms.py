from django import forms
from django.utils.timezone import now
from .models import Plan, StrategicGoal
from django import forms
from .models.kpi import KPI, Target  # Adjust import based on your structure

class PlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = ['year', 'quarter', 'month', 'week']
        widgets = {
            'year': forms.NumberInput(attrs={'placeholder': now().year}),
            'quarter': forms.TextInput(attrs={'placeholder': 'e.g. Q1'}),
            'month': forms.TextInput(attrs={'placeholder': 'e.g. January'}),
            'week': forms.TextInput(attrs={'placeholder': 'e.g. Week 1'}),
        }

    def save(self, commit=True, user=None):
        """
        Save the Plan instance and assign the user and level based on group.
        """
        instance = super().save(commit=False)
        if user:
            instance.user = user
            instance.level = user.groups.first().name.upper() if user.groups.exists() else 'INDIVIDUAL'
        if commit:
            instance.save()
        return instance


class StrategicGoalForm(forms.ModelForm):
    class Meta:
        model = StrategicGoal
        fields = ['title']  # Add 'description' if needed later
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Enter strategic goal title'})
        }

class PlanFilterForm(forms.Form):
    year = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'placeholder': 'Year'}))
    quarter = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'e.g. Q1'}))
    month = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'e.g. January'}))



class KPIForm(forms.ModelForm):
    class Meta:
        model = KPI
        fields = ['name', 'baseline', 'unit']


class TargetForm(forms.ModelForm):
    class Meta:
        model = Target
        fields = ['yearly', 'quarterly', 'monthly', 'weekly']
