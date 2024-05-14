from distutils.log import error
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
from django.contrib.auth.hashers import check_password



class UserList(APIView):

    
    def get(self, request):
        users = User.objects.filter(is_client=True)
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    def post(self, request):
        try:
            data_to_update = {'username':request.data.get('username') , 'password': request.data.get('password'), 'is_active': True, 'is_client': True, 'is_admin': False,'raw_password':request.data.get('password')}
            
            serializer = UserSerializer(data=data_to_update)
            
            if serializer.is_valid():
                
                serializer.save()
            
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print("e=",e.__context__)
            return Response(e, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
       
        withdrawal_requests = Account.objects.filter(ammount__gt=0)
        serializer = AccountSerializer(withdrawal_requests, many=True)
        print('withdrawal_requests=====,',serializer.data)

        

        account_statement = []

        for account in withdrawal_requests:

            acc_ste_dict  ={}
            acc_ste = AccountStatement.objects.filter(account=account)

            for acc_s in acc_ste:

                print(acc_s.withdraw)

                if acc_s.withdraw !=0:
                    acc_ste_dict['tnx'] = 'withdraw'
                else:
                    acc_ste_dict['tnx'] = 'deposit'

            account_statement.append(acc_ste_dict)



        account_and_statement = []
        withdraw_request_with_txn = zip(withdrawal_requests,account_statement)
        
        for zip_obj in withdraw_request_with_txn:

            account_and_statement.append(zip_obj)
        print(account_and_statement)
        context = {'withdrawal_requests': account_and_statement,'txn':account_and_statement}
        return self.render_to_response(context)

class ClientDashboard(APIView, TemplateView):
    

    template_name = 'dashboard_client.html'

    def get(self, request):
        
        print('request-user',request.user)
        withdrawal_requests = Account.objects.select_related('client').filter(client=request.user,withdraw_request_client=True)
        serializer = AccountSerializer(withdrawal_requests, many=True)
        

        

        account_statements = AccountStatement.objects.select_related('account').all()

        

        acc_ste_list=[]
        account_access = []
        acc_ste={}
        balance = 0
        for acc in account_statements:
            print("acc",acc)
            if acc and acc.account.client==request.user :
                print("hello")
                balance=acc.account.total_balnce
            # else:
            #   balance = 0


            
            
            if acc.account.account_bene is not None:
                if acc.withdraw != 0:
                    
                    acc_ste['txn'] = 'withdraw'
                    acc_ste['trn_date'] = acc.trn_date
                    acc_ste['paid_to'] = acc.account.account_bene.bene_account_name
                    acc_ste['acc_number'] = acc.account.account_bene.bene_account_number
                elif acc.deposit !=0:
                    acc_ste['txn'] = 'deposit'
                    acc_ste['trn_date'] = acc.trn_date
                    acc_ste['paid_to'] = acc.account.account_bene.bene_account_name
                    acc_ste['acc_number'] = acc.account.account_bene.bene_account_number

                acc_ste_list.append(acc_ste)
        
        print('acc_ste_list=',acc_ste_list)

        zip_acc_ste=zip(serializer.data,acc_ste_list)

        for zip_obj in zip_acc_ste:

            account_access.append(zip_obj)

        print("HELLO",account_access)

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
        acc_ste=AccountStatement.objects.select_related('account').filter(deposit=0)
       
        withdrawal_requests = Account.objects.filter(withdraw_request_client=True)
        serializer = AccountSerializer(withdrawal_requests, many=True)
        context = {'withdrawal_requests': serializer.data}
        return self.render_to_response(context)
       
    
    def post(self, request):
        try:
            print("USER=",request.user)
            print("USERSESSION=",request.session.get('email'))
            print("USER=",type(request.user.id))

            print("REQUESTED_DATA=",request.data)

            if request.user.is_admin:

                    
           
                    transaction_type = request.data['transaction_type']
                
                    if transaction_type.lower() == 'deposit':

                        withdraw_ste =  0

                        deposit_ste =  int(request.data['amount'])
                   
                        client = request.data['client']

                        print("client",client)

                       
                        
                        client_id=User.objects.get(email=client)

                        print("client_id",client_id)

                        

                        account_data = Account.objects.filter(client=client_id.id)

                        bene_details =  account_data.select_related('account_bene').last()

                        print("Bal=",bene_details)

                       

                        account_name = bene_details.account_bene

                        print("account_name=",account_data)

                        total_balance = bene_details.total_balnce + deposit_ste

                        print("Total balance=",total_balance)

                    
                    elif transaction_type.lower() == 'withdraw':

                        withdraw_ste =  int(request.data['amount'])

                        deposit_ste = 0

                        client = request.data['client']
                        print("client",client)
                        client_id=User.objects.get(email=client)

                        print("client_id",client_id)

                        account_data = Account.objects.filter(client=client_id.id)

                        bene_details =  account_data.select_related('account_bene').last()

                        print("Bal=",bene_details.total_balnce)

                      

                        account_name = bene_details.account_bene

                        print("Ammount=",int(request.data['amount']))

                        if bene_details.total_balnce >= int(request.data['amount']):

                            total_balance = bene_details.total_balnce - int(request.data['amount'])
                        else:
                            return Response(data={"Message":"Insufficient Balance"},status=status.HTTP_400_BAD_REQUEST)


                    print("HELLO========")

                    if account_name:

                    
                        data = {

                            'client':client_id.id,
                            'account_bene':account_name.id,
                            'ammount': int(request.data['amount']),
                            'account_name': account_name.bene_account_name,
                            'account_number':account_name.bene_account_number,
                            'branch_ifsc': account_name.bene_branch_ifsc,
                            'bank_name': account_name.bene_bank_name,
                            'req_status':'Approved',
                            'reasons':'NA',
                            'ref_number':0,
                            'total_balnce':total_balance,
                        
                        

                        }
                    else:

                        data = {

                            'client':client_id.id,
                            'account_bene':None,
                            'ammount': int(request.data['amount']),
                            'account_name': '',
                            'account_number':0,
                            'branch_ifsc': '',
                            'bank_name': '',
                            'req_status':'Approved',
                            'reasons':'NA',
                            'ref_number':0,
                            'total_balnce':total_balance,
                        
                        

                        }


                    serializer = AccountSerializer(data=data)
                    print("HELO----------------->> 2")
                    if serializer.is_valid():
                        print("HELO----------------->> 3")
                        serializer.save()

                        account_id = serializer.data['id']
                        ste_acc=   Account.objects.get(id=account_id)

                        print("main==",serializer.data)
                        account_statement_from_client_withdr = AccountStatement.objects.create(account=ste_acc,
                        deposit=deposit_ste,withdraw=withdraw_ste,trn_date=datetime.now())
                        return Response(serializer.data, status=status.HTTP_201_CREATED)
                    print(serializer.errors)
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                    

            else:   

                 
                    bene=   BeneficiaryDetails.objects.get(bene_account_number=int(request.data['anumber']))

                   
                    check_acc=Account.objects.all()

                   
                    check_acc = check_acc.filter(client=request.user)
                    

                    if len(check_acc) ==1:
                        check_acc.update(account_bene = bene)

                    account=check_acc.filter(account_bene=bene)
                   
                    

                
                    def dict_compare(d1, d2):
                        # Compare relevant keys
                        return d1.client == d2.client 

                    # Use a list comprehension to filter out duplicate dictionaries
                    account = [account[i] for i in range(len(account)) if all(not dict_compare(account[i], account[j]) for j in range(i+1, len(account)))]

                    if len(account)>0:

                        total_bal_ = account[-1].total_balnce
                    print('account',account)

                    print('total_bal',total_bal_)
                    
                    if  account and total_bal_ >= int(request.data['amount']):
                        data = {

                            'client':request.user.id,
                            'account_bene':bene.id,
                            'ammount': int(request.data['amount']),
                            'account_name': request.data['aname'],
                            'account_number':int(request.data['anumber']),
                            'branch_ifsc': request.data['abranch'],
                            'bank_name': request.data['bname'],
                            'req_status':'pending',
                            'reasons':'NA',
                            'ref_number':0,
                            'total_balnce': total_bal_,
                            'withdraw_request_client':True

                        }
                        

                        serializer = AccountSerializer(data=data)

                        account=Account.objects.filter(client__email=request.user)
                            

                        acc = account.last()

                        total_bal = account.last().total_balnce 
                    
                        if serializer.is_valid():
                        
                            serializer.save()
                            
                            account_id = serializer.data['id']

                            

                            req_status = Account.objects.get(id=account_id)
                           
                            if req_status.req_status == 'Approved': 
                                total_balance = total_bal-int(request.data['amount'])
                                account.update(total_balnce=total_balance)

                                

                            ste_acc=   Account.objects.get(id=account_id)

                            print("main==",serializer.data)
                            account_statement_from_client_withdr = AccountStatement.objects.create(account=ste_acc,
                            deposit=0,withdraw=int(request.data['amount']),trn_date=datetime.now()
                            )
                            
                            return Response(serializer.data, status=status.HTTP_201_CREATED)
                        print(serializer.errors)
                        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

                    return Response(data={"Message":"Insufficient Balance"},status=status.HTTP_400_BAD_REQUEST)
        except Exception as  e:
            return Response(e,status=status.HTTP_400_BAD_REQUEST)
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
       
        print(transaction_request.ammount)
        print(request.data)

        if request.data['req_status']=='approved':

            transaction_request.ref_number = request.data['ref_number']
            transaction_request.reasons = request.data['reasons']
        elif request.data['req_status']=='rejected':
            transaction_request.reasons = request.data['reasons']


        total_amt = transaction_request.total_balnce

        if request.data['transaction_type']:
           
            transaction_type = request.data['transaction_type']
           
            if transaction_type.lower() == 'withdraw':
                   
                    amount=transaction_request.ammount
                    print('total_balance',total_amt)
                    print('amount',amount)
                    if total_amt > int(amount):
                        
                        ammount = total_amt- int(amount)

                        transaction_request.ammount = int(amount)

                        transaction_request.total_balnce = ammount

                        client_with_request=AccountStatement.objects.all().last()
                        print("client_with_request",client_with_request)
                        client_with_request.account=transaction_request
                        client_with_request.deposit=0
                        client_with_request.withdraw=amount
                        client_with_request.trn_date=datetime.now()
                        client_with_request.save()

                        # AccountStatement.objects.create(account=transaction_request,deposit=0,withdraw=amount,trn_date=datetime.now())
                    else:
                        return Response(data={"Message":"Insufficent Balance"},status=status.HTTP_400_BAD_REQUEST)
            elif transaction_type.lower() == 'deposit':

                    amount=request.data['amount']

                    ammount = total_amt+ int(amount)

                    transaction_request.ammount =int(amount)
                    transaction_request.total_balnce = ammount
                    AccountStatement.objects.create(account=transaction_request,deposit=amount,withdraw=0,trn_date=datetime.now())
                    

        print("Request_data",request.data)            

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

            client_for = serializer.data['client']
            
            client = User.objects.get(id=client_for)

            account_q =Account.objects.filter(client=client)
            
            
            for acc in account_q:

                if acc.account_bene == None:

                    account_q.update(account_bene=serializer.data['id'])
                    
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(serializer.errors.values())
        return Response({'errors':serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

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
                request.session['user_id'] = user.id
                request.session['email'] = user.email
                return Response({'message': 'Login successful','user':'is_admin'}, status=status.HTTP_200_OK)
            elif user.is_client:
                login(request,user)
                request.session['user_id'] = user.id
                request.session['email'] = user.email
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
                    'client': client.email,
                    'created_at':client.created
            }

            print('client',client)
           
            # Retrieve account data for the current client
            account = Account.objects.filter(client__email=client.email)
            
            check_bene = BeneficiaryDetails.objects.all()  
           
            if  not account:
                if check_bene:
                    bene_account = BeneficiaryDetails.objects.get(client=client)

                    if bene_account:
                        print("bene_account")
                        first_account=Account.objects.create(client=client,account_bene=bene_account,
                        ammount=0,ref_number=0)
                        print('with bene')
                        client_data['id'] = first_account.id
                        client_data['ammount'] = first_account.ammount
                        client_data['total_balnce'] = first_account.total_balnce

                    
                    
                    context.append(client_data)

                else:
                    print('without bene')
                    first_account=Account.objects.create(client=client,account_bene=None,
                    ammount=0,ref_number=0)
                    client_data['id'] = first_account.id
                    client_data['ammount'] = first_account.ammount
                    client_data['total_balnce'] = first_account.total_balnce

                    

                    context.append(client_data)



                


            
            
            if account:
                    acc=   account.last()
                    
                    print("account",account)
                    print("account=",acc.id)
                    client_data['id'] = acc.id
                    client_data['ammount'] = acc.ammount
                   
                    client_data['total_balnce'] = acc.total_balnce
                    

                    
                    context.append(client_data)
            


        

       

        def dict_compare(d1, d2):
            # Compare relevant keys
            return d1['client'] == d2['client'] and d1['ammount'] == d2['ammount']

        # Use a list comprehension to filter out duplicate dictionaries
        context = [context[i] for i in range(len(context)) if all(not dict_compare(context[i], context[j]) for j in range(i+1, len(context)))]

       

        print(context)





        return render(request,self.template_name,context={"wallet":context})



class AccountStatementView(View):

        template_name = 'account_statement.html'

        def get(self, request):


            if request.user.is_client:
                acc_ste=AccountStatement.objects.all()


                context = []

                for acc_s in acc_ste:

                    

                    if request.user == acc_s.account.client and acc_s.account.req_status=='Approved':
                            print("hello")
                            account_statement = {
                                'txn_date': acc_s.trn_date,
                                'deposit': acc_s.deposit,
                                'withdraw': acc_s.withdraw,
                                'balance': acc_s.account.ammount
                            }
                            context.append(account_statement)

                

                # client_new = acc_ste.select_related('account').values('account__client').filter(account__client=request.user)

                client_new = Account.objects.select_related('client').values('client__email').filter(client__email=request.user)
                
                
                def dict_compare(d1, d2):
           
                        return d1['client__email'] == d2['client__email'] 

                    # Use a list comprehension to filter out duplicate dictionaries
                client_new    = [client_new[i] for i in range(len(client_new)) if all(not dict_compare(client_new[i], client_new[j]) for j in range(i+1, len(client_new)))]

               

                if  client_new:

                    if client_new[0]['client__email']==str(request.user):
                        acc=Account.objects.filter(client=request.user).last()
                
                       
                        balance=acc.total_balnce
                    else:
                        balance =0
                else:
                    balance =0
                

                print(context)

                


                return render(request,self.template_name,context={"account_statement":context,'balance':balance})
        
            return render(request,'login.html')
    


class BeneView(View):

    template_name = 'client_dashboard.html'

    def get(self, request):

        beneficiaries = BeneficiaryDetails.objects.select_related('client').filter(client=request.user)
        print('beneficiaries',beneficiaries)
        return render(request,self.template_name,{'bene':beneficiaries})






