from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

# Custom User Manager
class CustomUserManager(BaseUserManager):
    def create_user(self, mobile, password=None, **extra_fields):
        """Create and return a regular user with a mobile number and password."""
        if not mobile:
            raise ValueError("The Mobile field must be set")
        user = self.model(mobile=mobile, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, mobile, password=None, **extra_fields):
        """Create and return a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(mobile, password, **extra_fields)

class User(AbstractUser):

    firebase_uid = models.CharField(max_length=128, unique=True, null=True, blank=True)
    
    is_customer = models.BooleanField(default=False)
    is_vendor = models.BooleanField(default=False)

    mobile = models.CharField(max_length=15, unique=True)
    email = models.EmailField(null=True, blank=True)  # Email is optional

    username = None  # Remove username field

    USERNAME_FIELD = 'mobile'  # Set mobile as the login field
    REQUIRED_FIELDS = [] 

    objects = CustomUserManager()
