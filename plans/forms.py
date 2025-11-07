from django import forms
from django.forms import inlineformset_factory
from django.forms.models import BaseInlineFormSet
from django.core.exceptions import ValidationError
from decimal import Decimal

# Updated imports to reflect the new model structure
from .models import Plan, StrategicGoal, KPI, MajorActivity, DetailActivity


# --- Custom Base Formset for DetailActivity Validation ---
class BaseDetailActivityFormSet(BaseInlineFormSet):
    """
    Custom formset to validate that the sum of all child DetailActivity weights 
    equals the parent MajorActivity's total_weight.
    """
    def clean(self):
        super().clean()
        
        # Don't proceed if there are already validation errors on individual forms
        if any(self.errors):
            return

        # self.instance is the MajorActivity object this formset is bound to.
        major_activity = self.instance
        required_total_weight = major_activity.total_weight
        current_total_weight = Decimal('0.00')

        # We must have a required total weight on the parent to perform this check.
        if required_total_weight is None:
            # If no weight is set on the parent, skip the sum check, but we should 
            # ideally enforce total_weight in MajorActivityForm if children exist.
            # For simplicity, we rely on the MajorActivityForm to handle required fields.
            pass

        for form in self.forms:
            # Only process forms that have data and are not marked for deletion
            if form.cleaned_data and not form.cleaned_data.get('DELETE'):
                weight = form.cleaned_data.get('weight')
                if weight is not None:
                    current_total_weight += weight
        
        # Perform the main validation check against the parent's total_weight
        if required_total_weight is not None:
            # Check for a small tolerance (e.g., 0.01) to account for potential float/Decimal issues
            if abs(current_total_weight - required_total_weight) > Decimal('0.01'):
                raise ValidationError(
                    f"Weight Mismatch: The total weight of all Detail Activities ({current_total_weight:.2f}) "
                    f"must match the Major Activity's Total Weight ({required_total_weight:.2f})."
                )

# --- Detail Activity Form and Formset ---

class DetailActivityForm(forms.ModelForm):
    """
    Form for a single DetailActivity.
    """
    class Meta:
        model = DetailActivity
        fields = ['description', 'weight', 'responsible_person', 'status']
        widgets = {
            'description': forms.Textarea(attrs={'class': 'w-full px-2 py-1 border rounded-md text-sm', 'placeholder': 'Specific steps/tasks', 'rows': 2}),
            'weight': forms.NumberInput(attrs={'class': 'w-full px-2 py-1 border rounded-md text-sm', 'placeholder': 'Weight share'}),
            'responsible_person': forms.TextInput(attrs={'class': 'w-full px-2 py-1 border rounded-md text-sm', 'placeholder': 'Responsible'}),
            'status': forms.Select(attrs={'class': 'w-full px-2 py-1 border rounded-md text-sm'}),
        }

# Formset for DetailActivity, linked to MajorActivity (uses custom base class for validation)
DetailActivityFormset = inlineformset_factory(
    MajorActivity, 
    DetailActivity, 
    form=DetailActivityForm, 
    formset=BaseDetailActivityFormSet, # <--- Added custom base formset
    extra=1, 
    can_delete=True
)

# --- Strategic Goal Form and Formset ---

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
StrategicGoalFormset = inlineformset_factory(Plan, StrategicGoal, form=StrategicGoalForm, extra=1, can_delete=True)


# --- KPI Form and Formset (Unchanged) ---

class KPIForm(forms.ModelForm):
    """
    Form for a single KPI.
    """
    class Meta:
        model = KPI
        fields = ['name', 'measurement','baseline', 'target','target_q1','target_q2','target_q3','target_q4']

        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'Enter the KPI name'}),
            'measurement': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'e.g., Percentage, Count'}),
            'baseline': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'Enter the baseline value'}),
            'target': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'Enter the target value'}),
            'target_q1': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'Enter Q1 target value'}),
            'target_q2': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'Enter Q2 target value'}),
            'target_q3': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'Enter Q3 target value'}),
            'target_q4': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'Enter Q4 target value'}),
        }
        
    def __init__(self, *args, **kwargs):
        # Retrieve plan_type if provided, defaulting to 'yearly' for safety
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
            
            # Check 1: Ensure all quarterly targets are provided if the form is active
            if any(q is None for q in q_values) and (self.has_changed() or self.instance.pk):
                for field_name in q_fields:
                    if cleaned_data.get(field_name) is None:
                        self.add_error(field_name, "Required for a Yearly Plan.")
                        
                q_values = [cleaned_data.get(f) for f in q_fields]

            # Check 2: Progressive Target Validation (Q1 <= Q2 <= Q3 <= Q4)
            if all(q is not None for q in q_values):
                if not (q_values[0] <= q_values[1] <= q_values[2] <= q_values[3]):
                    raise forms.ValidationError(
                        "Quarterly targets must be progressive (non-decreasing): Q1 ≤ Q2 ≤ Q3 ≤ Q4."
                    )
                
                # Check 3: Total Target must equal Q4 Target
                q4_target = q_values[3]
                
                if yearly_target is None:
                    self.add_error('target', "Total target is required for a Yearly Plan.")
                
                # Check within a small tolerance for floating point numbers
                elif abs(yearly_target - q4_target) > 0.001: 
                     self.add_error('target', 
                         f"Target Mismatch: The Total Target ({yearly_target}) must exactly equal the Q4 Target ({q4_target}) for progressive metrics."
                        )

        return cleaned_data    
# Set can_delete=True to automatically include the hidden fields for deletion.
KPIFormset = inlineformset_factory(Plan, KPI, form=KPIForm, extra=1, can_delete=True)


# --- Major Activity Form and Formset ---

class MajorActivityForm(forms.ModelForm):
    """
    Form for a single MajorActivity.
    """
    class Meta:
        model = MajorActivity
        fields = ['name', 'total_weight', 'budget']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-md font-semibold', 'placeholder': 'e.g., Q2 Marketing Campaign'}),
            'total_weight': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'Total weight for this Major Activity'}),
            'budget': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'Total budget (e.g., 5000.00)'}),
        }
    
    # Custom cleaning to ensure total_weight is required if the form is being submitted
    def clean_total_weight(self):
        total_weight = self.cleaned_data.get('total_weight')
        # We only strictly require total_weight if the activity name is provided (i.e., the user is trying to save it)
        if self.cleaned_data.get('name') and total_weight is None:
            raise forms.ValidationError("Total weight is required for a Major Activity.")
        return total_weight


# Formset for MajorActivity, linked to Plan (used on the main Plan form)
MajorActivityFormset = inlineformset_factory(Plan, MajorActivity, form=MajorActivityForm, extra=1, can_delete=True)


# --- Plan Creation Form (Unchanged) ---

class PlanCreationForm(forms.ModelForm):
    """
    The main form for the Plan model, which will be used in conjunction with the formsets.
    """
    # Use ChoiceField with the choices from the Plan model
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
        if plan_type == 'weekly' and not cleaned_data.get('week_number'):
            self.add_error('week_number', 'Week number is required for a weekly plan.')
        if plan_type == 'monthly' and not cleaned_data.get('month'):
            self.add_error('month', 'Month is required for a monthly plan.')
        if plan_type == 'quarterly' and not cleaned_data.get('quarter_number'):
            self.add_error('quarter_number', 'Quarter number is required for a quarterly plan.')
        
        return cleaned_data