from django.contrib import admin
from .models import Plan, StrategicGoal, KPI, MajorActivity, DetailActivity

# --- 1. Detail Activity Inline (Lowest Level) ---

class DetailActivityInline(admin.TabularInline):
    """Inline for managing DetailActivity models within a MajorActivity."""
    model = DetailActivity
    extra = 1
    fields = [
        'description', 
        'weight', 
        'responsible_person', 
        'status'
    ]
    # Use raw_id_fields for foreign keys if you expect many records, but usually not needed for inlines
    # raw_id_fields = ('major_activity',) 


# --- 2. Major Activity Inline (Mid-Level, contains Detail Inline) ---

class MajorActivityInline(admin.StackedInline):
    """Inline for managing MajorActivity models within a Plan. This is the NESTED part."""
    model = MajorActivity
    extra = 1
    # Fields for the Major Activity itself
    fields = [
        'name', 
        'total_weight', 
        'budget'
    ]
    # NESTED INLINE: Include Detail Activities here
    inlines = [DetailActivityInline]


# --- Existing Inlines ---

class StrategicGoalInline(admin.TabularInline):
    model = StrategicGoal
    extra = 1
    fields = ['title']


class KPIInline(admin.TabularInline):
    model = KPI
    extra = 1
    fields = [
        'name', 
        'measurement', 
        'baseline', 
        'target', 
        ('target_q1', 'target_q2', 'target_q3', 'target_q4') # Group quarterly targets
    ] 
    # Use max_num=4 to limit the number of KPIs, if necessary (e.g., if you only want 4 KPIs per plan)


# --- Plan Admin (Top Level) ---

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "user",
        "level",
        "plan_type",
        "year",
        "status",
        "total_budget", # Display the calculated total budget property from the Plan model
        "created_at",
    )
    list_display_links = ("__str__",)
    list_filter = ("level", "plan_type", "status")
    search_fields = ("user__username", "level", "plan_type")
    
    # Inlines are listed here. MajorActivityInline now brings its DetailActivity children.
    inlines = [StrategicGoalInline, KPIInline, MajorActivityInline] 
    
    date_hierarchy = "created_at"

# Register remaining models to be visible in the Admin interface (optional but good practice)
admin.site.register(StrategicGoal)
admin.site.register(KPI)
admin.site.register(MajorActivity)
admin.site.register(DetailActivity)