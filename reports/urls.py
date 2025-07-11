from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # http://127.0.0.1:8000/
    path('corporate/', views.corporate_dashboard, name='corporate_dashboard'),  # http://127.0.0.1:8000/corporate/
    path('view/', views.view_plans, name='view_plans'),  # ✅ http://127.0.0.1:8000/view/
    path('plans/<int:plan_id>/add-goals/', views.add_goals_to_plan, name='add_goals'),  # http://127.0.0.1:8000/plans/1/add-goals/
    path('plans/<int:plan_id>/goals/', views.view_goals, name='view_goals'),  # http://127.0.0.1:8000/plans/1/goals/
    path('plans/create/', views.create_plan, name='create_plan'),
    path('goals/<int:goal_id>/add-kpis/', views.add_kpis_to_goal, name='add_kpis'),
    path('kpis/<int:kpi_id>/add-targets/', views.add_targets_to_kpi, name='add_targets'),

]
