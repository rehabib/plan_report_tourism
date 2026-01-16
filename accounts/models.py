from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser

# class User(AbstractUser):
#     # You can add additional fields here if needed
#     ROLE_CHOICES = (
        
#         ("individual", "Individual"),
#         ("desk", "Desk"),
#         ("department", "Department"),
#         ("corporate", "Corporate"),
#         ("state-minister-destination", "State Minister - Destination"),
#         ("state-minister-promotion", "State Minister - Promotion"),
#         ("strategic-team", "Strategic Team"),
#         ("minister", "Minister"),
    
#     )
#     role = models.CharField(
#         max_length=40,
#         choices=ROLE_CHOICES,
#         default="individual"
#     )

#     department = models.CharField(
#         max_length=100,
#         blank=True,
#         null=True
#     )

#     def __str__(self):
#         return f"{self.username} ({self.role})"
    
class User(AbstractUser):
    ROLE_CHOICES = [
        ("individual", "Individual"),
        ("desk", "Desk"),
        ("department", "Department"),
        ("corporate", "Corporate"),
        ("state-minister-destination", "State Minister - Destination"),
        ("state-minister-promotion", "State Minister - Promotion"),
        ("strategic-team", "Strategic Team"),
        ("minister", "Minister"),
    ]

    role = models.CharField(max_length=40, choices=ROLE_CHOICES, default="individual")

    department = models.ForeignKey(
        "plans.Department",
        on_delete=models.SET_NULL,
        max_length=100,
        null=True,
        blank=True,
        related_name="users"
    )

    desk = models.ForeignKey(   # OPTIONAL but recommended
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="desk_members"
    )

    def __str__(self):
        return f"{self.username} ({self.role})"
   