from django.urls import path
from . import views

urlpatterns = [
    path("create/<int:plan_id>/", views.create_report, name="create_report"),
    path("view/<int:report_id>/", views.view_report, name="view_report"),
    
    path("approve/<int:report_id>/", views.approve_report, name="approve_report"),
    path("reject/<int:report_id>/", views.reject_report, name="reject_report"),
]
