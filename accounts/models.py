from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # You can add additional fields here if needed
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('CORPORATE', 'corporate'),
        ('DEPARTMENT', 'Department'),
        ('INDIVIDUAL', 'Individual'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='INDIVIDUAL')
    def __str__(self):
        return f"{self.username} ({self.role})"