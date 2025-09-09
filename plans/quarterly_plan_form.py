from django.forms import modelform_factory, modelformset_factory, inlineformset_factory
from .models import QuarterlyPlan, KPI, StrategicGoal, Activity

QuarterlyPlanForm = modelform_factory(QuarterlyPlan, fields='__all__')

KPIFormSet = inlineformset_factory(
    QuarterlyPlan, KPI,
    fields=['name', 'baseline', 'target', 'accountable_person', 'budget'],
    extra=1, can_delete=True
)

StrategicGoalFormSet = inlineformset_factory(
    QuarterlyPlan, StrategicGoal,
    fields=['title', 'description'],
    extra=1, can_delete=True
)

ActivityFormSet = inlineformset_factory(
    QuarterlyPlan, Activity,
    fields=['major_activity', 'detail_activity', 'responsible_person', 'budget', 'status'],
    extra=1, can_delete=True
)
