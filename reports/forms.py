from django import forms
from .models import Report

class ReportCreationForm(forms.ModelForm):
    """
    A form to create a new report for a specific plan.
    """
    class Meta:
        model = Report
        fields = ['plan', 'report_type', 'date', 'period', 'goal', 'kpi', 'achieved_value', 'budget_used', 'comment']
        widgets = {
            'plan': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-md'}),
            'report_type': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-md'}),
            'date': forms.DateInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'type': 'date'}),
            'period': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'e.g., Week 1, Q1'}),
            'goal': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-md'}),
            'kpi': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-md'}),
            'achieved_value': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'Value achieved'}),
            'budget_used': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'Budget used'}),
            'comment': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'placeholder': 'Add your comments here'}),
        }
