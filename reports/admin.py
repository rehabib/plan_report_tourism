from django.contrib import admin
from .models import (
    Plan,
    StrategicGoal,
    KPI,
    Target,
    Activity,
    Report,
)

# Display inline related models
class StrategicGoalInline(admin.TabularInline):
    model = StrategicGoal
    extra = 1

class ActivityInline(admin.TabularInline):
    model = Activity
    extra = 1

class ReportInline(admin.TabularInline):
    model = Report
    extra = 1

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'level', 'year', 'quarter', 'month', 'week', 'created_at']
    list_filter = ['level', 'year', 'quarter', 'month']
    search_fields = ['user__username', 'level']
    inlines = [StrategicGoalInline, ActivityInline, ReportInline]

@admin.register(StrategicGoal)
class StrategicGoalAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'plan']
    search_fields = ['title', 'plan__user__username']

@admin.register(KPI)
class KPIAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'baseline', 'unit', 'goal']
    search_fields = ['name', 'goal__title']

@admin.register(Target)
class TargetAdmin(admin.ModelAdmin):
    list_display = ['id', 'kpi', 'yearly', 'quarterly', 'monthly', 'weekly']

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ['id', 'plan', 'major_activity']
    search_fields = ['major_activity', 'plan__user__username']

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'plan', 'user', 'title', 'submitted_at']
    search_fields = ['title', 'user__username', 'plan__level']
