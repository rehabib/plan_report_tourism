from django import forms
from django.forms import inlineformset_factory
from .models import WeeklyPlan, MonthlyPlan, QuarterlyPlan, YearlyPlan
from .models import KPI, StrategicGoal, Activity

# --- Plan Forms ---
class WeeklyPlanForm(forms.ModelForm):
    class Meta:
        model = WeeklyPlan
        exclude = ['user', 'created_at']

class MonthlyPlanForm(forms.ModelForm):
    class Meta:
        model = MonthlyPlan
        exclude = ['user', 'created_at']

class QuarterlyPlanForm(forms.ModelForm):
    class Meta:
        model = QuarterlyPlan
        exclude = ['user', 'created_at']

class YearlyPlanForm(forms.ModelForm):
    class Meta:
        model = YearlyPlan
        exclude = ['user', 'created_at']

# --- Formsets ---
KPIFormSet = inlineformset_factory(
    parent_model=WeeklyPlan,  # Will be replaced dynamically in views
    model=KPI,
    fields=('name', 'baseline', 'target', 'accountable_person', 'budget'),
    extra=1,
    can_delete=True
)

StrategicGoalFormSet = inlineformset_factory(
    parent_model=WeeklyPlan,  # Will be replaced dynamically in views
    model=StrategicGoal,
    fields=('title', 'description'),
    extra=1,
    can_delete=True
)

ActivityFormSet = inlineformset_factory(
    parent_model=WeeklyPlan,  # Will be replaced dynamically in views
    model=Activity,
    fields=('major_activity', 'detail_activity', 'responsible_person', 'budget', 'status'),
    extra=1,
    can_delete=True
)
