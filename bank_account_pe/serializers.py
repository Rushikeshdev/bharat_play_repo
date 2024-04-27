from rest_framework import serializers
from .models import *


class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='email')
    class Meta:
        model = User
        fields = ['username','password' ,'is_active', 'is_client', 'is_admin',]


class WithdrawalRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = WithdrawalRequest
        fields = '__all__'



class BeneficiaryDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BeneficiaryDetails
        fields = '__all__'