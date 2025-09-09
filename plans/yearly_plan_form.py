from django.forms import modelform_factory, modelformset_factory, inlineformset_factory
from .models import YearlyPlan, KPI, StrategicGoal, Activity

YearlyPlanForm = modelform_factory(YearlyPlan, fields='__all__')

KPIFormSet = inlineformset_factory(
    YearlyPlan, KPI,
    fields=['name', 'baseline', 'target', 'accountable_person', 'budget'],
    extra=1, can_delete=True
)

StrategicGoalFormSet = inlineformset_factory(
    YearlyPlan, StrategicGoal,
    fields=['title', 'description'],
    extra=1, can_delete=True
)

ActivityFormSet = inlineformset_factory(
    YearlyPlan, Activity,
    fields=['major_activity', 'detail_activity', 'responsible_person', 'budget', 'status'],
    extra=1, can_delete=True
)
