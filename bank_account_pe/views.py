from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import *
from django.http import Http404
from .serializers import *
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.contrib.auth import logout


class UserList(APIView):

    
    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    def post(self, request):
        data_to_update = {'username':request.data.get('username') , 'password': request.data.get('password'), 'is_active': False, 'is_client': True, 'is_admin': False}
        
        serializer = UserSerializer(data=data_to_update)
        
        if serializer.is_valid():
            
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserDetail(APIView):
    def get_object(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        user = self.get_object(pk)
        serializer = UserSerializer(user)
        return Response(serializer.data)

    def put(self, request, pk):
        user = self.get_object(pk)
        serializer = UserSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        user = self.get_object(pk)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminDashboard(APIView, TemplateView):
    

    template_name = 'admin_dashboard.html'

    def get(self, request):
       
        withdrawal_requests = WithdrawalRequest.objects.all()
        serializer = WithdrawalRequestSerializer(withdrawal_requests, many=True)
        context = {'withdrawal_requests': serializer.data}
        return self.render_to_response(context)

class ClientDashboard(APIView, TemplateView):
    

    template_name = 'dashboard_client.html'

    def get(self, request):
       
        withdrawal_requests = WithdrawalRequest.objects.all()
        serializer = WithdrawalRequestSerializer(withdrawal_requests, many=True)
        context = {'withdrawal_requests': serializer.data}
        return self.render_to_response(context)



class WithdrawalRequestList(APIView, TemplateView):

    html_template_client = 'client_main_dashboard.html'

    html_template_admin = 'admin_withdrawal_request.html'
    
    template_name = ''

    

    def get(self, request):
       

        if request.user.is_client:

            self.template_name = self.html_template_client
        else:

            self.template_name = self.html_template_admin

        withdrawal_requests = WithdrawalRequest.objects.all()
        serializer = WithdrawalRequestSerializer(withdrawal_requests, many=True)
        context = {'withdrawal_requests': serializer.data}
        return self.render_to_response(context)

    def post(self, request):


        data = {
            'ammount': int(request.data['amount']),
            'account_name': request.data['aname'],
            'account_number':int(request.data['anumber']),
            'branch_ifsc': request.data['abranch'],
            'bank_name': request.data['bname']

        }

        serializer = WithdrawalRequestSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class WithdrawalRequestDetail(APIView):
    def get_object(self, pk):
        try:
            return WithdrawalRequest.objects.get(pk=pk)
        except WithdrawalRequest.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        withdrawal_request = self.get_object(pk)
        serializer = WithdrawalRequestSerializer(withdrawal_request)
        return Response(serializer.data)

    def put(self, request, pk):
        withdrawal_request = self.get_object(pk)
        serializer = WithdrawalRequestSerializer(withdrawal_request, data=request.data,partial=True)
        if serializer.is_valid():
           
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        withdrawal_request = self.get_object(pk)
        withdrawal_request.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)




class BeneficiaryDetailsList(APIView):
    def get(self, request):
        beneficiaries = BeneficiaryDetails.objects.all()
        serializer = BeneficiaryDetailsSerializer(beneficiaries, many=True)
        return Response(serializer.data)

    def post(self, request):
        print('data=',request.data)
        
        data = {

            'bene_account_name':request.data['name'],
            'bene_account_number': int(request.data['accountnumber']),
            'bene_bank_name': request.data['bankname'],
            'bene_branch_ifsc':request.data['bankifsc'],
            'created_at':datetime.now()

        }

        serializer = BeneficiaryDetailsSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BeneficiaryDetailsDetail(APIView):
    def get_object(self, pk):
        try:
            return BeneficiaryDetails.objects.get(pk=pk)
        except BeneficiaryDetails.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        beneficiary = self.get_object(pk)
        serializer = BeneficiaryDetailsSerializer(beneficiary)
        return Response(serializer.data)

    def put(self, request, pk):
        beneficiary = self.get_object(pk)
        serializer = BeneficiaryDetailsSerializer(beneficiary, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        beneficiary = self.get_object(pk)
        beneficiary.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



class UserLogin(APIView):
    def post(self, request):
        # Extract username and password from request data
        username = request.data.get('username')
        password = request.data.get('password')
        
        # Authenticate user
        user = authenticate(username=username, password=password)

        print(user)
       

        # Check if authentication was successful
        if user is not None:
            # User is authenticated, return success response
            return Response({'message': 'Login successful','user':user.is_superuser}, status=status.HTTP_200_OK)
        else:
            # Authentication failed, return error response
            return Response({'error': 'Invalid username or password'}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutAPIView(APIView,TemplateView):

    template_name = 'login.html'

    def post(self, request):
        try:
            
            
            logout(request)
            return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)