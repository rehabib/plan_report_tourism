from django import forms
from django.forms import inlineformset_factory
from .models import Plan, StrategicGoal, KPI, Activity

class StrategicGoalForm(forms.ModelForm):
    """
    Form for a single StrategicGoal.
    """
    class Meta:
        model = StrategicGoal
        fields = ['title']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'Enter a strategic goal'}),
        }
        
# Set can_delete=True to automatically include the hidden fields for deletion.
# The custom JavaScript from the previous response will handle the "Remove" button.
StrategicGoalFormset = inlineformset_factory(Plan, StrategicGoal, form=StrategicGoalForm, extra=1, can_delete=True)

class KPIForm(forms.ModelForm):
    """
    Form for a single KPI.
    """
    class Meta:
        model = KPI
        fields = ['name', 'baseline', 'target']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'Enter the KPI name'}),
            'baseline': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'Enter the baseline value'}),
            'target': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'Enter the target value'}),
        }
        
# Set can_delete=True to automatically include the hidden fields for deletion.
KPIFormset = inlineformset_factory(Plan, KPI, form=KPIForm, extra=1, can_delete=True)


class ActivityForm(forms.ModelForm):
    """
    Form for a single Activity.
    """
    class Meta:
        model = Activity
        fields = ['major_activity', 'detail_activity', 'responsible_person', 'budget']
        widgets = {
            'major_activity': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'e.g., Conduct market research'}),
            'detail_activity': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'Provide detailed steps for the activity'}),
            'responsible_person': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'Name of accountable person'}),
            'budget': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'Allocated budget'}),
        }

# Set can_delete=True to automatically include the hidden fields for deletion.
ActivityFormset = inlineformset_factory(Plan, Activity, form=ActivityForm, extra=1, can_delete=True)


class PlanCreationForm(forms.ModelForm):
    """
    The main form for the Plan model, which will be used in conjunction with the formsets.
    """
    # Use ChoiceField with the choices from the Plan model
    # The 'month' field can be an empty string, which is fine as it's not required.
    month = forms.ChoiceField(
        choices=[('', 'Select a Month')] + list(Plan.MONTH_CHOICES),
        required=False,
        label="Month",
        widget=forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-md'})
    )

    class Meta:
        model = Plan
        fields = ['plan_type', 'year', 'week_number', 'month', 'quarter_number']
        widgets = {
            'plan_type': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-md'}),
            'year': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'e.g., 2024'}),
            'week_number': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'e.g., 1-4'}),
            'quarter_number': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'e.g., 1-4'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        plan_type = cleaned_data.get('plan_type')
        week_number = cleaned_data.get('week_number')
        month = cleaned_data.get('month')
        quarter_number = cleaned_data.get('quarter_number')

        # Set specific fields to None if they are empty strings
        if month == '':
            cleaned_data['month'] = None
        if week_number == '':
            cleaned_data['week_number'] = None
        if quarter_number == '':
            cleaned_data['quarter_number'] = None

        # Add validation logic based on the plan type
        if plan_type == 'weekly' and not week_number:
            self.add_error('week_number', 'Week number is required for a weekly plan.')
        if plan_type == 'monthly' and not month:
            self.add_error('month', 'Month is required for a monthly plan.')
        if plan_type == 'quarterly' and not quarter_number:
            self.add_error('quarter_number', 'Quarter number is required for a quarterly plan.')
        
        return cleaned_data
