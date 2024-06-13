from http import client
from django.db import models
from datetime import datetime
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager,PermissionsMixin

# Create your models here.

class UserManager(BaseUserManager):
    def create_user(self, email, password=None):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None):
        """
        Creates and saves a superuser with the given email and password.
        """
        user = self.create_user(
            email,
            password=password,
        )
        user.is_admin     = True
        user.is_active    = True
        user.is_superadmin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
    )
    
    raw_password = models.CharField(max_length=128)
    created     = models.DateTimeField(auto_now_add=True)
    is_active       = models.BooleanField(default=True, help_text = 'Enable or disable user account')
  
    is_staff = models.BooleanField(
        default=False,
        help_text=("Designates whether the user can log into this admin site."),
    )
    is_superadmin      = models.BooleanField(default=False)
    is_admin           = models.BooleanField(default=False)
    is_client           = models.BooleanField(default=False)

   


   

    objects         = UserManager()

    USERNAME_FIELD = 'email'

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        return self.is_admin
    
    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
	    # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
	    # Simplest possible answer: Yes, always
        return True

    def __str__(self):
        return f'{self.email}'


        



class BeneficiaryDetails(models.Model):
    client = models.ForeignKey(User, on_delete=models.CASCADE,related_name='client_bene')
    bene_account_name = models.CharField(max_length=255,blank=True,null=True)
    bene_account_number = models.BigIntegerField(unique=True)
    bene_branch_ifsc = models.CharField(max_length=255,blank=True,null=True)
    bene_bank_name = models.CharField(max_length=255,blank=True,null=True)
    created_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.bene_account_name},{self.bene_account_number}"


class Account(models.Model):

    client = models.ForeignKey(User, on_delete=models.CASCADE,related_name='client')
    account_bene = models.ForeignKey(BeneficiaryDetails, on_delete=models.CASCADE,related_name='bene',null=True)
    ammount = models.IntegerField()
    req_status = models.CharField(max_length=255,default='pending')
    reasons = models.CharField(max_length=255,default='')
    admin_remark = models.CharField(max_length=255,default='')
    ref_number = models.CharField(max_length=255)
    total_balnce = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now=True)
    withdraw_request_client = models.BooleanField(default=False)
    status_change_by = models.CharField(max_length=255,default='')
    withdrawal_today = models.IntegerField(default=0)
    withdrawal_day = models.DateField()
    withdrawal_request_accepted_by = models.CharField(max_length=255,default='Pending')



    def __str__(self):
        return f"{self.account_bene},{self.ammount}"



class AccountStatement(models.Model):

    account = models.ForeignKey(Account, on_delete=models.CASCADE,related_name='account')
    deposit = models.IntegerField()
    withdraw = models.IntegerField()
    trn_date = models.DateTimeField()

    def __str__(self):
        return f"{self.account},{self.trn_date}"







        