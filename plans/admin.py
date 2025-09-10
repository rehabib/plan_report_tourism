from django.contrib import admin
from .models import Plan, StrategicGoal, KPI, Activity

# Register your models here.

class StrategicGoalInline(admin.TabularInline):
    model = StrategicGoal
    extra = 1
    fields = ['title']

class KPIInline(admin.TabularInline):
    model = KPI
    extra = 1
    fields = ['name', 'baseline', 'target']

class ActivityInline(admin.StackedInline):
    model = Activity
    extra = 1
    fields = ['major_activity', 'detail_activity', 'responsible_person', 'budget', 'status']

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "user",
        "level",
        "plan_type",
        "year",
        "status",
        "created_at",
    )
    list_display_links = ("__str__",)
    list_filter = ("level", "plan_type", "status")
    search_fields = ("user__username", "level", "plan_type")
    inlines = [StrategicGoalInline, KPIInline, ActivityInline]
    date_hierarchy = "created_at"
