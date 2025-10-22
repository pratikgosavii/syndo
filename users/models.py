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


class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class User(AbstractUser):
    firebase_uid = models.CharField(max_length=128, unique=True, null=True, blank=True)

    is_customer = models.BooleanField(default=False)
    is_vendor = models.BooleanField(default=False)
    is_subuser = models.BooleanField(default=False)

    pincode = models.IntegerField()

    mobile = models.CharField(max_length=15, unique=True)
    email = models.EmailField(null=True, blank=True)

    username = None
    USERNAME_FIELD = 'mobile'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()


class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'role')

    def __str__(self):
        return f"{self.user} - {self.role}"


class MenuModule(models.Model):
    title = models.CharField(max_length=100)
    url_name = models.CharField(max_length=100)
    icon_class = models.CharField(max_length=100, blank=True, null=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')

    def __str__(self):
        return self.title


class RoleMenuPermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    menu_module = models.ForeignKey(MenuModule, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('role', 'menu_module')



class DeviceToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=255)  # FCM token
    updated_at = models.DateTimeField(auto_now=True)
