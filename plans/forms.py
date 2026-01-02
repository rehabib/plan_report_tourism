from django import forms
from django.forms import inlineformset_factory
from django.forms.models import BaseInlineFormSet
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import Plan, StrategicGoal, KPI, MajorActivity, DetailActivity
from django.contrib.auth import get_user_model

# Get the User Model for ForeignKey fields
User = get_user_model()

# Base Tailwind class for inputs
INPUT_CLASS = 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 transition duration-150 ease-in-out shadow-sm'

class BaseDetailActivityFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

        total_weight = Decimal("0.00")

        for form in self.forms:
            if self.can_delete and form.cleaned_data.get("DELETE"):
                continue
            if not form.cleaned_data:
                continue

            weight = form.cleaned_data.get("weight")
            if weight:
                total_weight += weight

        major_weight = self.instance.weight

        if total_weight != major_weight:
            raise ValidationError(
                f"Total detail activity weight ({total_weight}) "
                f"must equal major activity weight ({major_weight})."
            )
class PlanCreationForm(forms.ModelForm):
    """
    The main form for the Plan model, which will be used in conjunction with the formsets.
    """
    # Using forms.ChoiceField to allow for an empty initial selection
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
            'week_number': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'e.g., 1-52'}),
            'quarter_number': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'e.g., 1-4'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        plan_type = cleaned_data.get('plan_type')

        # Clean up empty strings from ChoiceFields (month is an integer field in model)
        if cleaned_data.get('month') == '':
            cleaned_data['month'] = None
        
        # Ensure that non-required fields are None if blank, to match the model (especially NumberInputs)
        for field in ['week_number', 'quarter_number']:
             if cleaned_data.get(field) == '':
                cleaned_data[field] = None

        # Add validation logic based on the plan type
        if plan_type == 'weekly' and not cleaned_data.get('week_number'):
            self.add_error('week_number', 'Week number is required for a weekly plan.')
        if plan_type == 'monthly' and not cleaned_data.get('month'):
            self.add_error('month', 'Month is required for a monthly plan.')
        if plan_type == 'quarterly' and not cleaned_data.get('quarter_number'):
            self.add_error('quarter_number', 'Quarter number is required for a quarterly plan.')
        
        return cleaned_data
    

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
        
StrategicGoalFormset = inlineformset_factory(Plan, StrategicGoal, form=StrategicGoalForm, extra=1, can_delete=True)


# --- KPI Form and Formset ---

class KPIForm(forms.ModelForm):
    """
    Form for a single KPI.
    Handles progressive target validation for Yearly Plans.
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
            
            # --- Check 1: Ensure quarterly targets are provided ---
            if any(q is None for q in q_values) and (self.has_changed() or self.instance.pk):
                for field_name in q_fields:
                    if cleaned_data.get(field_name) is None:
                        self.add_error(field_name, "Required for a Yearly Plan.")
                        
                q_values = [cleaned_data.get(f) for f in q_fields]

            # --- Check 2: Progressive Target Validation (Q1 <= Q2 <= Q3 <= Q4) ---
            # if all(q is not None for q in q_values):
            #     if not (q_values[0] <= q_values[1] <= q_values[2] <= q_values[3]):
            #         raise forms.ValidationError(
            #             "Quarterly targets must be progressive (non-decreasing): Q1 ≤ Q2 ≤ Q3 ≤ Q4."
            #         )
                
                # --- Check 3: Total Target must equal Q4 Target ---
                q4_target = q_values[0]+ q_values[1]+ q_values[2] + q_values[3] 
                
                if yearly_target is None:
                    self.add_error('target', "Total target is required for a Yearly Plan.")
                
                # Check within a small tolerance for floating point numbers
                # elif abs(yearly_target - q4_target) > 0.001: 
                #      self.add_error('target', 
                #          f"Target Mismatch: The Total Target ({yearly_target}) must exactly equal the Q4 Target ({q4_target}) for progressive metrics."
                #         )

        return cleaned_data    
KPIFormset = inlineformset_factory(Plan, KPI, form=KPIForm, extra=1, can_delete=True)


# MAJOR ACTIVITY FORMSET

class MajorActivityForm(forms.ModelForm):
    """
    Form for a single Major Activity.
    The budget is the editable field here.
    """
    class Meta:
        model = MajorActivity
        # *** CORRECTED: Removed calculated properties (total_weight, total_budget) ***
        fields = ['major_activity','weight', 'budget', 'responsible_person'] 

        widgets = {
            'major_activity': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Major Activity Title'}),
            # Budget is the editable field
            'weight': forms.NumberInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Weight (e.g., 25.00)'}), 
            'budget': forms.NumberInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Allocated Budget'}), 
            'responsible_person': forms.Select(attrs={'class': INPUT_CLASS}), # Use Select for ForeignKey
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optional: Set queryset for responsible person
        self.fields['responsible_person'].queryset = User.objects.all().order_by('username')


MajorActivityFormset = inlineformset_factory(
    Plan,
    MajorActivity,
    form=MajorActivityForm,
    extra=1,
    can_delete=True
)


# --- DETAIL ACTIVITY FORMSET ---

class DetailActivityForm(forms.ModelForm):
    """
    Form for a single Detail Activity.
    Weight is the editable field here.
    """
    class Meta:
        model = DetailActivity
        # *** CORRECTED: Removed 'budget' which is not a field on DetailActivity model ***
        fields = ['detail_activity', 'weight', 'responsible_person', 'status']

        widgets = {
            'detail_activity': forms.Textarea(attrs={
                'class': INPUT_CLASS,
                'rows': 2,
                'placeholder': 'Detailed steps to complete the Major Activity',
            }),
            'weight': forms.NumberInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Weight (e.g., 25.00)'}),
            'responsible_person': forms.Select(attrs={'class': INPUT_CLASS}), # Use Select for ForeignKey
            'status': forms.Select(attrs={'class': INPUT_CLASS}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optional: Set queryset for responsible person
        self.fields['responsible_person'].queryset = User.objects.all().order_by('username')


DetailActivityFormset = inlineformset_factory(
    MajorActivity,
    DetailActivity,
    form=DetailActivityForm,
    formset=BaseDetailActivityFormSet,
    extra=1,
    can_delete=True
)