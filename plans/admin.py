from django.contrib import admin
from django.db.models import Sum
from .models import Plan, StrategicGoal, KPI, MajorActivity, DetailActivity
from .models import Department



@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "pillar")
    list_filter = ("pillar",)
    search_fields = ("name",)
    ordering = ("pillar", "name")

# --- 1. Detail Activity Inline (Lowest Level) ---

class DetailActivityInline(admin.TabularInline):
    model = DetailActivity
    extra = 1
    max_num = 10

    fields = [
        'detail_activity',  
        'weight',  
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
    # fields = [
    #     'major_activity',  
    #     'budget',  
    #     'responsible_person'
      
    # ]

    # Fields that are calculated properties and should only be displayed (read-only)
    readonly_fields = [
        'weight', 
    ]

    # Group the editable fields and the read-only calculated field for a nice display
    fieldsets = (
        (None, {
            'fields': (
                ('major_activity', 'responsible_person'),
                ('budget', 'weight'), # Display budget next to its calculated weight
            ),
        }),
    )

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
        "get_total_budget", 
        "created_at",
    )
    list_display_links = ("__str__",)
    list_filter = ("level", "plan_type", "status")
    search_fields = ("user__username", "level", "plan_type")
    
    # Inlines are listed here. MajorActivityInline now brings its DetailActivity children.
    inlines = [StrategicGoalInline, KPIInline, MajorActivityInline]  

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
    readonly_fields = (
    "status",
    "current_reviewer_role",
    "pillar",
    "created_at",
)
    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return [f.name for f in self.model._meta.fields]
        return self.readonly_fields

    
    date_hierarchy = "created_at"
    
    # This calls the @property method on the Plan model
    def get_total_budget(self, obj):
        return obj.total_budget
    get_total_budget.short_description = 'Total Budget'
    get_total_budget.admin_order_field = 'major_activities__budget'
# Register remaining models to be visible in the Admin interface (optional but good practice)
# admin.site.register(StrategicGoal)
# admin.site.register(KPI)
# admin.site.register(MajorActivity)
# admin.site.register(DetailActivity)