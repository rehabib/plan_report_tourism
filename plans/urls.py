from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('', views.dashboard, name='dashboard'),
    path('create_plan/', views.create_plan, name='create_plan'),
    path('edit/<int:plan_id>/', views.edit_plan, name='edit_plan'),
    path('plans/success/<int:plan_id>/', views.plan_success, name='plan_success'),
    path('plans/<int:plan_id>/', views.view_plan, name='view_plan'),
     path('delete/<int:plan_id>/', views.delete_plan, name='delete_plan'),

]
