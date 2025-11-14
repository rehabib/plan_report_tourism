from django.contrib import admin
from .models import Plan, StrategicGoal, KPI, MajorActivity, DetailActivity

# --- Import custom forms and formsets for validation ---
# We need to import the custom form and formset class to enforce the budget/weight constraints
from .forms import DetailActivityForm, BaseDetailActivityFormSet

# --- 1. Detail Activity Inline (Lowest Level) ---

class DetailActivityInline(admin.TabularInline):
    """
    Inline for managing DetailActivity models within a MajorActivity.
    
    CRUCIAL: We assign the custom form and formset here to enable the 
    weight/budget sum validation upon saving the MajorActivity.
    """
    model = DetailActivity
    extra = 1
    # ASSIGN CUSTOM FORM and FORMSET for complex validation
    form = DetailActivityForm 
    formset = BaseDetailActivityFormSet 
    
    fields = [
        'description',  
        'weight',  
        'budget',  # <-- FIX: Added the missing budget field
        'responsible_person',  
        'status'
    ]


# --- 2. Major Activity Inline (Mid-Level, contains Detail Inline) ---

class MajorActivityInline(admin.StackedInline):
    """
    Inline for managing MajorActivity models within a Plan. 
    This is the NESTED part.
    """
    model = MajorActivity
    extra = 1
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
    """
    KPI Inline. Note: Admin inlines do not use formset validation directly,
    so the complex progressive target validation will run when the form 
    is validated in the admin view.
    """
    model = KPI
    extra = 1
    fields = [
        'name',  
        'measurement',  
        'baseline',  
        'target',  
        ('target_q1', 'target_q2', 'target_q3', 'target_q4') # Group quarterly targets
    ]  
    
    # You could optionally assign KPIForm here if you needed to pass extra context 
    # to its __init__ (like plan_type), but for basic admin functionality, this is often skipped.


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
        "total_budget", 
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