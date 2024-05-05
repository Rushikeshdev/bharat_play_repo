from rest_framework import serializers
from .models import *


class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='email')
    class Meta:
        model = User
        fields = ['username','password' ,'is_active', 'is_client', 'is_admin',]
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'



class BeneficiaryDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BeneficiaryDetails
        fields = '__all__'


# class ClientWalletListSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ClientWalletList
#         fields = '__all__'