from rest_framework import serializers
from .models import *
from django.contrib.auth.hashers import make_password

class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='email')
    password = serializers.CharField(write_only=True)
    created = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = User
        fields = ['id','username','password' ,'is_active', 'is_client', 'is_admin','raw_password','created']
    
    

    def create(self, validated_data):
        # Extract and encrypt the password before creating the user
        password = validated_data.pop('password')
        validated_data['password'] = make_password(password)  # Encrypt password
        user = User.objects.create(**validated_data)
        return user
    


    def to_representation(self, instance):
        # Override to_representation to include password in original form
        representation = super().to_representation(instance)
        request = self.context.get('request', None)
        if request and request.method == 'GET':
            representation['created'] = self.get_created_formatted(instance)
        representation['password'] = instance.raw_password  # Display original password
        return representation

    def get_created_formatted(self, obj):
        # Format the created date
        return obj.created.strftime("%b %d, %Y, %I:%M %p")

class BeneficiaryDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BeneficiaryDetails
        fields = '__all__'


class AccountSerializer(serializers.ModelSerializer):
    client_email = serializers.SerializerMethodField()
    created_at_formatted = serializers.SerializerMethodField()
    account_bene_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Account
        fields = '__all__'
        # depth = 1 # Include one level of related objects (account_bene in this case)
    def get_client_email(self, obj):
        # Access the email of the related client User
        return obj.client.email

    def get_created_at_formatted(self, obj):
        return obj.created_at.strftime("%b %d, %Y, %I:%M %p")


    def get_account_bene_details(self, obj):
        request = self.context.get('request')
    
        if request and request.method == 'GET' and obj.account_bene:
            return BeneficiaryDetailsSerializer(obj.account_bene).data
        return None



class ClientWalletSerializer(serializers.ModelSerializer):

         class Meta:
            model = ClientWallet
            fields = '__all__'
