from django.contrib import admin
from .models import Report

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'report_type', 'plan', 'date', 'period', 'performance', 'created_at']
    list_filter = ['report_type', 'plan__user__username']
    search_fields = ['report_type', 'plan__user__username']
