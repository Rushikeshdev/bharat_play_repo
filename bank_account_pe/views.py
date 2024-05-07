from typing import Any
from django.http.response import HttpResponse as HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import *
from django.http import Http404, HttpRequest
from .serializers import *
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.contrib.auth import logout,login
from django.views import View
from django.shortcuts import render


class UserList(APIView):

    
    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    def post(self, request):
        data_to_update = {'username':request.data.get('username') , 'password': request.data.get('password'), 'is_active': True, 'is_client': True, 'is_admin': False}
        
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
       
        withdrawal_requests = Account.objects.all()
        serializer = AccountSerializer(withdrawal_requests, many=True)
        context = {'withdrawal_requests': serializer.data}
        return self.render_to_response(context)

class ClientDashboard(APIView, TemplateView):
    

    template_name = 'dashboard_client.html'

    def get(self, request):
        
        print('request-user',request.user)
        withdrawal_requests = Account.objects.select_related('client').filter(client=request.user)
        serializer = AccountSerializer(withdrawal_requests, many=True)
        
        if len(withdrawal_requests) >0:
            balance=withdrawal_requests[0].ammount
        else:
            balance = 0

        account_statements = AccountStatement.objects.select_related('account').all()

        acc_ste_list=[]
        account_access = []
        for acc in account_statements:
            acc_ste={}

            if acc.withdraw != 0:

                acc_ste['txn'] = 'withdraw'
            elif acc.deposit !=0:
                acc_ste['txn'] = 'deposit'

            acc_ste_list.append(acc_ste)
        
       

        zip_acc_ste=zip(serializer.data,acc_ste_list)

        for zip_obj in zip_acc_ste:

            account_access.append(zip_obj)

        print(account_access)

        context = {'withdrawal_requests': account_access,'balance':balance,'acc_ste':acc_ste_list}
        return self.render_to_response(context)



 
    

    
class WithdrawalRequestList(APIView, TemplateView):

    html_template_client = 'client_main_dashboard.html'

    html_template_admin = 'admin_withdrawal_request.html'
    
    template_name = ''

    

    
    
    def get(self, request):
        # Check if the user is authenticated
        
        if request.user.is_authenticated:
            print('REQUEST',request.user)
            if request.user.is_admin:
                print('is_admin...')
                self.template_name = self.html_template_admin
            elif request.user.is_client:
                self.template_name = self.html_template_client
        else:
            print("not auth...")
            self.template_name = 'login.html'

        withdrawal_requests = Account.objects.all()
        serializer = AccountSerializer(withdrawal_requests, many=True)
        context = {'withdrawal_requests': serializer.data}
        return self.render_to_response(context)

    def post(self, request):

        print("USER=",request.user.id)

        print("USER=",type(request.user.id))

        data = {

            'client':request.user.id,
            'ammount': int(request.data['amount']),
            'account_name': request.data['aname'],
            'account_number':int(request.data['anumber']),
            'branch_ifsc': request.data['abranch'],
            'bank_name': request.data['bname'],
            'req_status':'pending',
            'reasons':'NA',
            'ref_number':0

        }
        

        serializer = AccountSerializer(data=data)
       
        if serializer.is_valid():
            serializer.save()

            account=Account.objects.filter(client__email=request.user)
            

            acc = account.last()
           
            account_statement_from_client_withdr = AccountStatement.objects.create(account=acc,
            deposit=0,withdraw=int(request.data['amount']),trn_date=datetime.now()
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class WithdrawalRequestDetail(APIView):
    def get_object(self, pk):
        try:
            return Account.objects.get(pk=pk)
        except Account.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        withdrawal_request = self.get_object(pk)
        serializer = AccountSerializer(withdrawal_request)
        return Response(serializer.data)

    def put(self, request, pk):
        transaction_request = self.get_object(pk)
        print('MYDATA',request.data)

        if request.data['req_status']=='approved':

            transaction_request.ref_number = request.data['ref_number']
            transaction_request.reasons = request.data['reasons']
        elif request.data['req_status']=='rejected':
            transaction_request.reasons = request.data['reasons']


        total_amt = transaction_request.ammount

        if request.data['transaction_type']:
           
            transaction_type = request.data['transaction_type']
            print('hello...',request.data['transaction_type'])
            if transaction_type.lower() == 'withdraw':
                    print('hello...')
                    amount=request.data['amount']

                    ammount = total_amt- int(amount)

                    transaction_request.ammount = ammount

                    AccountStatement.objects.create(account=transaction_request,deposit=0,withdraw=amount,trn_date=datetime.now())

            elif transaction_type.lower() == 'deposit':

                    amount=request.data['amount']

                    ammount = total_amt+ int(amount)

                    transaction_request.ammount = ammount
                    AccountStatement.objects.create(account=transaction_request,deposit=amount,withdraw=0,trn_date=datetime.now())

                

        serializer = AccountSerializer(transaction_request, data=request.data,partial=True)
        if serializer.is_valid():
           
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        withdrawal_request = self.get_object(pk)
        withdrawal_request.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)




class BeneficiaryDetailsList(APIView,View):
    def get(self, request):
        beneficiaries = BeneficiaryDetails.objects.all()
        serializer = BeneficiaryDetailsSerializer(beneficiaries, many=True)
        return Response(serializer.data)

    def post(self, request):
        print('data=',request.data)
        
        data = {
            'client':request.user.id,
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


# class ClientWalletList(APIView,TemplateView):

    



class UserLogin(APIView):
    def post(self, request):
        # Extract username and password from request data
        username = request.data.get('username')
        password = request.data.get('password')
        print(username)
        print(password)
        # Authenticate user
        user = authenticate(request,email=username, password=password)

        print(user)
       
        print(user.is_authenticated)
        # Check if authentication was successful
        if user is not None:
            # User is authenticated, return success response
            
            if user.is_admin:
                login(request,user)
                print('is_admin')
                return Response({'message': 'Login successful','user':'is_admin'}, status=status.HTTP_200_OK)
            elif user.is_client:
                login(request,user)
                return Response({'message': 'Login successful','user':'is_client'}, status=status.HTTP_200_OK)


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



class WalletListView(View):

    template_name = 'admin_client_wallet.html'

    def get(self, request):

        client =User.objects.filter(is_client=True)

        context =[]

        for client in client:

            client_data = {
                    'client': client.email
            }

            

            # Retrieve account data for the current client
            account = Account.objects.filter(client__email=client.email)

            
            
            for account in account:
                print("account=",account.id)
                client_data['id'] = account.id
                client_data['ammount'] = account.ammount
                client_data['created_at'] = account.created_at

                
                context.append(client_data)
                


        

        print(context)


        return render(request,self.template_name,context={"wallet":context})



class AccountStatementView(View):

        template_name = 'account_statement.html'

        def get(self, request):


            if request.user.is_client:
                acc_ste=AccountStatement.objects.all()



                context = []

                for acc_s in acc_ste:

                    
                   print(request.user)
                   print(acc_s.account.client)
                   if request.user == acc_s.account.client:
                    
                        account_statement = {
                            'txn_date': acc_s.trn_date,
                            'deposit': acc_s.deposit,
                            'withdraw': acc_s.withdraw,
                            'balance': acc_s.account.ammount
                        }
                        context.append(account_statement)

                

                # client_new = acc_ste.select_related('account').values('account__client').filter(account__client=request.user)

                client_new = Account.objects.select_related('client').values('client__email').get(client__email=request.user)
                
                if client_new['client__email']==str(request.user):
                    acc=Account.objects.get(client=request.user)
                   
                    balance=acc.ammount
                else:
                    balance =0

                print(context)

                print()


                return render(request,self.template_name,context={"account_statement":context,'balance':balance})
        
            return render(request,'login.html')
    


class BeneView(View):

    template_name = 'client_dashboard.html'

    def get(self, request):

        beneficiaries = BeneficiaryDetails.objects.select_related('client').filter(client=request.user)
        print('beneficiaries',beneficiaries)
        return render(request,self.template_name,{'bene':beneficiaries})






