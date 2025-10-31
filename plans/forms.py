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
        fields = ['name', 'measurement','weight','baseline', 'target','target_q1','target_q2','target_q3','target_q4']

        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'Enter the KPI name'}),
            'measurement': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'e.g., Percentage, Count'}),
            'weight': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'Enter the weight'}),
            'baseline': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'Enter the baseline value'}),
            'target': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'Enter the target value'}),
            'target_q1': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'Enter Q1 target value'}),
            'target_q2': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'Enter Q2 target value'}),
            'target_q3': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'Enter Q3 target value'}),
            'target_q4': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'Enter Q4 target value'}),
        }
        
    def __init__(self, *args, **kwargs):
        self.plan_type = kwargs.pop('plan_type', 'yearly') 
        super().__init__(*args, **kwargs)
        
        for q_field in ['target_q1', 'target_q2', 'target_q3', 'target_q4']:
            self.fields[q_field].required = False

    def clean(self):
        cleaned_data = super().clean()
        
        if self.plan_type == 'yearly':
            q_fields = ['target_q1', 'target_q2', 'target_q3', 'target_q4']
            q_values = [cleaned_data.get(f) for f in q_fields]
            yearly_target = cleaned_data.get('target')
            
            # --- Check 1: Ensure all quarterly targets are provided ---
            if any(q is None for q in q_values):
                if self.has_changed() or self.instance.pk:
                    for field_name in q_fields:
                        if cleaned_data.get(field_name) is None:
                            self.add_error(field_name, "Required for a Yearly Plan.")
                    
                    # Re-collect cleaned data to check the next rules
                    q_values = [cleaned_data.get(f) for f in q_fields]

            # --- Check 2: Progressive Target Validation (Q1 <= Q2 <= Q3 <= Q4) ---
            if all(q is not None for q in q_values):
                if not (q_values[0] <= q_values[1] <= q_values[2] <= q_values[3]):
                    raise forms.ValidationError(
                        "Quarterly targets must be progressive (non-decreasing): Q1 ≤ Q2 ≤ Q3 ≤ Q4."
                    )
            
                # --- Check 3: Total Target must equal Q4 Target ---
                q4_target = q_values[3]
                
                if yearly_target is None:
                    self.add_error('target', "Total target is required for a Yearly Plan.")
                
                elif abs(yearly_target - q4_target) > 0.001: 
                     self.add_error('target', 
                        f"Target Mismatch: The Total Target ({yearly_target}) must exactly equal the Q4 Target ({q4_target}) for progressive metrics."
                     )

        return cleaned_data     
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
