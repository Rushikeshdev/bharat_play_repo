from rest_framework import serializers
from .models import *
from django.contrib.auth.hashers import make_password

class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='email')
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username','password' ,'is_active', 'is_client', 'is_admin','raw_password']
    
    # def create(self, validated_data):
    #     password = validated_data.pop('password')
    #     user = User.objects.create(**validated_data)
    #     user.set_password(password)
    #     user.save()
    #     return user

    def create(self, validated_data):
        # Extract and encrypt the password before creating the user
        password = validated_data.pop('password')
        validated_data['password'] = make_password(password)  # Encrypt password
        user = User.objects.create(**validated_data)
        return user
    
    def to_representation(self, instance):
        # Override to_representation to include password in original form
        representation = super().to_representation(instance)
        representation['password'] = instance.raw_password  # Display original password
        print(representation)
        return representation




class AccountSerializer(serializers.ModelSerializer):
    client_email = serializers.SerializerMethodField()
    created_at_formatted = serializers.SerializerMethodField()
    class Meta:
        model = Account
        fields = '__all__'
    def get_client_email(self, obj):
        # Access the email of the related client User
        return obj.client.email

    def get_created_at_formatted(self, obj):
        return obj.created_at.strftime("%b %d, %Y, %I:%M %p")




class BeneficiaryDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BeneficiaryDetails
        fields = '__all__'


# class ClientWalletListSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ClientWalletList
#         fields = '__all__'