from django.urls import path
from . import views as view


urlpatterns = [
    path('select-plan-type/', view.select_plan_type_view, name='select_plan_type'),
    path('create-plan/', view.create_plan_view, name='create_plan'),
    path('plans/', view.plan_list_view, name='plan_list'),  # list of user's plans

]
