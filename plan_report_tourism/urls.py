from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),  # 👈 point to your accounts app
    path('plans/', include('plans.urls')),  # 👈 point to your app (adjust app name if not "plans")
]
