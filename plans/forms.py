from django import forms
from .models import Plan, StrategicGoal, KPI, Activity

class PlanCreationForm(forms.ModelForm):
    """
    A single form to handle the creation of a Plan and its related models.
    """
    goal_title = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'Enter a strategic goal'}))
    kpi_name = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'Enter the KPI name'}))
    kpi_baseline = forms.FloatField(required=True, widget=forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'Enter the baseline value'}))
    kpi_target = forms.FloatField(required=True, widget=forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'Enter the target value'}))
    major_activity = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'e.g., Conduct market research'}))
    detail_activity = forms.CharField(widget=forms.Textarea(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'Provide detailed steps for the activity'}), required=True)
    responsible_person = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'Name of accountable person'}))
    budget = forms.DecimalField(max_digits=12, decimal_places=2, required=True, widget=forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'Allocated budget'}))

    class Meta:
        model = Plan
        fields = ['plan_type', 'year', 'week_number', 'month', 'quarter_number']
        widgets = {
            'plan_type': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-md'}),
            'year': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'e.g., 2024'}),
            'week_number': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'e.g., 1-4'}),
            'month': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'e.g., 1-12'}),
            'quarter_number': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'e.g., 1-4'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        plan_type = cleaned_data.get('plan_type')
        week_number = cleaned_data.get('week_number')
        month = cleaned_data.get('month')
        quarter_number = cleaned_data.get('quarter_number')

        # Add validation logic based on the plan type
        if plan_type == 'weekly' and not week_number:
            self.add_error('week_number', 'Week number is required for a weekly plan.')
        if plan_type == 'monthly' and not month:
            self.add_error('month', 'Month is required for a monthly plan.')
        if plan_type == 'quarterly' and not quarter_number:
            self.add_error('quarter_number', 'Quarter number is required for a quarterly plan.')
        if plan_type == 'yearly' and (month or week_number or quarter_number):
            raise forms.ValidationError("Yearly plans do not require a specific week, month, or quarter.")

        return cleaned_data
