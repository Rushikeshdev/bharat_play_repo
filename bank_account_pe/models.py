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
    created_at = models.DateTimeField(auto_now=True)
    withdraw_request_client = models.BooleanField(default=False)
    status_change_by = models.CharField(max_length=255,default='')
    withdrawal_today = models.IntegerField(default=0)
    withdrawal_day = models.DateField()
    withdrawal_request_accepted_by = models.CharField(max_length=255,default='Pending')
    remark_for_client = models.CharField(max_length=255,default='',blank=True,null=True)
    updated_at = models.DateTimeField(auto_now=True)
  

    def save(self, *args, **kwargs):
            super().save(*args, **kwargs)


    def __str__(self):

        if self.account_bene is not None:
            return f"{self.account_bene},{self.ammount}"
        
        return f"Transaction Done by SuperAdmin {self.ammount}"


class ClientWallet(models.Model):

    client = models.OneToOneField(User, on_delete=models.CASCADE,related_name='user')
    client_wallet_total_balance = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.client},{self.client_wallet_total_balance}"



class AccountStatement(models.Model):

    account = models.ForeignKey(Account, on_delete=models.CASCADE,related_name='account',null=True, blank=True)
    clientwallet = models.ForeignKey(ClientWallet, on_delete=models.CASCADE,related_name='clientwallet')
    account_tnx_status = models.CharField(max_length=255,default='pending')
    deposit = models.IntegerField()
    withdraw = models.IntegerField()
    statement_balance = models.IntegerField(default=0)
    admin_remark_superadmin = models.CharField(max_length=255,null=True,blank=True)
    utr_number_superadmin_narration = models.CharField(max_length=255,null=True,blank=True)
    trn_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Convert trn_date and updated_at to local time before saving
        now_utc = datetime.utcnow()
        trn_date = timezone.localtime(timezone.make_aware(now_utc, timezone.utc))
        updated_at = timezone.localtime(timezone.make_aware(now_utc, timezone.utc))
        self.trn_date = trn_date.strftime('%Y-%m-%d %H:%M')
        self.updated_at = updated_at.strftime('%Y-%m-%d %H:%M')
        super().save(*args, **kwargs)

    def __str__(self):

        if self.account is not None:
            return f"{self.account},{self.trn_date}"

        else:
             return f"{self.clientwallet},{self.trn_date}"











        