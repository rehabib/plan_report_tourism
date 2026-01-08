from django.urls import path
from . import views

urlpatterns = [
    path("create/<int:plan_id>/", views.create_report, name="create_report"),
    path("<int:report_id>/", views.view_report, name="view_report"),
]
