# authentication_backends.py
from django.contrib.auth import get_user_model

class CustomUser1Backend:
    def authenticate(self, request, username=None, password=None):
        User = get_user_model()
       
        try:
            user = User.objects.get(email=username)  # Assuming email is the unique identifier for CustomUser1
            
            if user.check_password(password) or user.password == password:
                print("user",user)
                return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

class CustomUser2Backend:
    def authenticate(self, request, username=None, password=None):
        User = get_user_model()
        try:
            user = User.objects.get(email=username)  # Assuming username is the unique identifier for CustomUser2
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
