from django.contrib import admin
from .models import (
    WeeklyPlan,
    MonthlyPlan,
    QuarterlyPlan,
    YearlyPlan,
    StrategicGoal,
    KPI,
    Activity,
    Report,
)

# --- Plan Admins ---
@admin.register(WeeklyPlan)
class WeeklyPlanAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'year', 'week_number', 'created_at']
    list_filter = ['year', 'week_number']
    search_fields = ['user__username']

@admin.register(MonthlyPlan)
class MonthlyPlanAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'year', 'month', 'created_at']
    list_filter = ['year', 'month']
    search_fields = ['user__username']

@admin.register(QuarterlyPlan)
class QuarterlyPlanAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'year', 'quarter', 'created_at']
    list_filter = ['year', 'quarter']
    search_fields = ['user__username']

@admin.register(YearlyPlan)
class YearlyPlanAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'year', 'created_at']
    list_filter = ['year']
    search_fields = ['user__username']


# --- Inline Models (optional) ---
class StrategicGoalInline(admin.TabularInline):
    model = StrategicGoal
    extra = 1

class ActivityInline(admin.TabularInline):
    model = Activity
    extra = 1

class ReportInline(admin.TabularInline):
    model = Report
    extra = 1


# --- Related Models ---
@admin.register(StrategicGoal)
class StrategicGoalAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'get_plan']
    search_fields = ['title']

    def get_plan(self, obj):
        return str(obj.content_object)
    get_plan.short_description = 'Plan'


@admin.register(KPI)
class KPIAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'baseline', 'target', 'get_plan']
    search_fields = ['name']

    def get_plan(self, obj):
        return str(obj.content_object)
    get_plan.short_description = 'Plan'


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ['id', 'major_activity', 'status', 'get_plan']
    search_fields = ['major_activity']

    def get_plan(self, obj):
        return str(obj.content_object)
    get_plan.short_description = 'Plan'


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'user', 'submitted_at', 'get_plan']
    search_fields = ['title', 'user__username']

    def get_plan(self, obj):
        return str(obj.content_object) if hasattr(obj, "content_object") else "-"
    get_plan.short_description = 'Plan'
