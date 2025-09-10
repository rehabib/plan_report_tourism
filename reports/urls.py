from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_reports, name='list_reports'),
    path('create/<int:plan_id>/', views.create_report, name='create_report'),
]
