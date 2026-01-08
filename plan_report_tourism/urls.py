from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('plans.urls')), # Main app for plans and reports
    path('reports/', include('reports.urls')), # New reports app
    path('accounts/', include('accounts.urls')), # For any future account-related views
    

]
