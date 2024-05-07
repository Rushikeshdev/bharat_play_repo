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
    client_email = serializers.SerializerMethodField()
    class Meta:
        model = Account
        fields = '__all__'
    def get_client_email(self, obj):
        # Access the email of the related client User
        return obj.client.email



class BeneficiaryDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BeneficiaryDetails
        fields = '__all__'


# class ClientWalletListSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ClientWalletList
#         fields = '__all__'