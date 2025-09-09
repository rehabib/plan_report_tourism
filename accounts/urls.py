from django.urls import path
from .views import register_view, CustomLoginView, role_select_view

urlpatterns = [
    path('select-role/', role_select_view, name='select_role'),
    path('register/', register_view, name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
]
