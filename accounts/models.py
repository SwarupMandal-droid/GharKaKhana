from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):

    def create_user(self, email, phone, name, role, password=None):
        if not email:
            raise ValueError('Email is required')
        if not phone:
            raise ValueError('Phone is required')

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            phone=phone,
            name=name,
            role=role,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, phone, name, password):
        user = self.create_user(
            email=email,
            phone=phone,
            name=name,
            role=User.Role.ADMIN,
            password=password,
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):

    class Role(models.TextChoices):
        CUSTOMER = 'CUSTOMER', 'Customer'
        COOK     = 'COOK',     'Cook'
        DELIVERY = 'DELIVERY', 'Delivery Person'
        ADMIN    = 'ADMIN',    'Admin'

    email      = models.EmailField(unique=True)
    phone      = models.CharField(max_length=15, unique=True)
    name       = models.CharField(max_length=100)
    role       = models.CharField(max_length=20, choices=Role.choices)
    is_active  = models.BooleanField(default=True)
    is_staff   = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['phone', 'name']

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f'{self.name} ({self.role})'

    def is_cook(self):
        return self.role == self.Role.COOK

    def is_customer(self):
        return self.role == self.Role.CUSTOMER

    def is_delivery(self):
        return self.role == self.Role.DELIVERY

    def is_admin_user(self):
        return self.role == self.Role.ADMIN