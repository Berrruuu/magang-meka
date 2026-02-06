from django.db import models
from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.base_user import BaseUserManager


class Company(models.Model):
    name = models.CharField(max_length=100)
    x_active = models.BooleanField(default=True)

    class Meta:
        db_table = "company"

    def __str__(self):
        return self.name


class KpiTarget(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, db_column="company_id")
    kpi = models.CharField(max_length=100)
    tahun = models.IntegerField()

    jan_01 = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    feb_02 = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    mar_03 = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    apr_04 = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    may_05 = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    jun_06 = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    jul_07 = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    aug_08 = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    sep_09 = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    oct_10 = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    nov_11 = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    des_12 = models.DecimalField(max_digits=20, decimal_places=2, default=0)

    setahun = models.DecimalField(max_digits=25, decimal_places=2, default=0)
    note = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.kpi} - {self.company.name} - {self.tahun}"
    


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email wajib diisi")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=50)
    company = ArrayField(models.IntegerField())
    status = models.BooleanField(default=True)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "users"
        managed = False  

    def __str__(self):
        return self.email
