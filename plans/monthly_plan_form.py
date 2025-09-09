from django.forms import modelform_factory, modelformset_factory, inlineformset_factory
from .models import MonthlyPlan, KPI, StrategicGoal, Activity

MonthlyPlanForm = modelform_factory(MonthlyPlan, fields='__all__')

KPIFormSet = inlineformset_factory(
    MonthlyPlan, KPI,
    fields=['name', 'baseline', 'target', 'accountable_person', 'budget'],
    extra=1, can_delete=True
)

StrategicGoalFormSet = inlineformset_factory(
    MonthlyPlan, StrategicGoal,
    fields=['title', 'description'],
    extra=1, can_delete=True
)

ActivityFormSet = inlineformset_factory(
    MonthlyPlan, Activity,
    fields=['major_activity', 'detail_activity', 'responsible_person', 'budget', 'status'],
    extra=1, can_delete=True
)
