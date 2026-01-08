from django import forms
from django.forms import inlineformset_factory
from .models import Report, KPIReport, MajorActivityReport
from .utils import get_kpi_target



class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ["overall_comment"] #eddittale



class KPIReportForm(forms.ModelForm):
    expected_target = forms.FloatField(
        label="Planned Target",
        disabled=True,
        required=False
    )

    class Meta:
        model = KPIReport
        fields = ["actual_value", "remark"]

    def __init__(self, *args, **kwargs):
        plan = kwargs.pop("plan", None)
        super().__init__(*args, **kwargs)

        if plan and self.instance.pk:
            target = get_kpi_target(self.instance.kpi, plan)
            self.fields["expected_target"].initial = target


class BaseKPIReportFormSet(forms.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        self.plan = kwargs.pop("plan", None)
        super().__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        kwargs["plan"] = self.plan
        return super()._construct_form(i, **kwargs)


KPIReportFormSet = inlineformset_factory(
    Report,
    KPIReport,
    form=KPIReportForm,
    formset=BaseKPIReportFormSet,
    extra=0,
    can_delete=False
)



MajorActivityReportFormSet = inlineformset_factory(
    Report,
    MajorActivityReport,
    fields=[
        "progress",
        "actual_budget_used",
        "challenge",
        "mitigation"
    ],
    extra=0,
    can_delete=False
) 

