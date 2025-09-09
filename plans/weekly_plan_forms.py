from django.forms import modelform_factory, inlineformset_factory
from .models import WeeklyPlan, KPI, StrategicGoal, Activity

WeeklyPlanForm = modelform_factory(WeeklyPlan, fields='__all__')

WeeklyKPIFormSet = inlineformset_factory(
    WeeklyPlan, KPI,
    fk_name='weekly_plan',  # must match ForeignKey field in KPI
    fields=['name', 'baseline', 'target', 'accountable_person', 'budget'],
    extra=1, can_delete=True
)

WeeklyGoalFormSet = inlineformset_factory(
    WeeklyPlan, StrategicGoal,
    fk_name='weekly_plan',
    fields=['title', 'description'],
    extra=1, can_delete=True
)

WeeklyActivityFormSet = inlineformset_factory(
    WeeklyPlan, Activity,
    fk_name='weekly_plan',
    fields=['major_activity', 'detail_activity', 'responsible_person', 'budget', 'status'],
    extra=1, can_delete=True
)
