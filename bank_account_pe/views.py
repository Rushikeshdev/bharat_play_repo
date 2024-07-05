from distutils.log import error
import re
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
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.dateparse import parse_date



def local_time():

    now_utc = datetime.utcnow()

    # Convert UTC time to the local time
    now_local = timezone.localtime(timezone.make_aware(now_utc, timezone.utc))
    print("NOW",now_local)
    return now_local

def custom_404(request, exception=None):
    print(request)
    return render(request, 'templates/login.html', status=404)

class UserList(LoginRequiredMixin,APIView,TemplateView):

    client_template = 'client.html'

    admin_template  = 'admin.html'


    def get(self, request):

  
        try:
            
            print(timezone.get_current_timezone())
            if request.user.is_superadmin and "admintemplate" in request.build_absolute_uri():
                self.template_name = self.admin_template
                users = User.objects.filter(is_superadmin=False ,is_admin=True)

               

                serializer = UserSerializer(users, many=True,context={'request':request})

                user_data_with_wallet = []
                for user in serializer.data:
                   
                    account = Account.objects.filter(withdrawal_request_accepted_by=user['username']).last()

                    with_today = Account.objects.filter(withdrawal_request_accepted_by=user['username'],req_status='Approved',withdrawal_day=datetime.now().date()).values('ammount').order_by('-created_at')

                    withdrwal_amount = sum(item['ammount'] for item in with_today)


                    wallet_data = {
                        'id': account.id if account else None,
                        'total_balance': 0,
                        'withdrawal_today': withdrwal_amount  if account else 0,
                        
                    }

                    # Combine user data with wallet data
                    user_with_wallet = {
                        **user,
                        'wallet': wallet_data
                    }
                    user_data_with_wallet.append(user_with_wallet)

                context_wallet_user={'users':user_data_with_wallet}
                
            elif request.user.is_superadmin or request.user.is_admin:
                
                self.template_name = self.client_template

                users = User.objects.filter(is_client=True)
                serializer = UserSerializer(users, many=True,context={'request': request})

                #Client Wallet

                user_data_with_wallet = []
                for user in serializer.data:
                   
                    # account = Account.objects.filter(client__email=user['username'],req_status='Approved').last()

                    try:

                        client_wallet = ClientWallet.objects.get(client__email=user['username'])

                        with_today = Account.objects.filter(client__email=user['username'],req_status='Approved',withdrawal_day=datetime.now().date(),withdraw_request_client=True).values('ammount').order_by('-created_at')

                        withdrwal_amount = sum(item['ammount'] for item in with_today)

                        wallet_data = {
                            'id': client_wallet.id if client_wallet else None,
                            'total_balance': client_wallet.client_wallet_total_balance if client_wallet else 0,
                            'withdrawal_today': withdrwal_amount if withdrwal_amount else 0
                        }
                    except ClientWallet.DoesNotExist:
                            # Handle the case where the ClientWallet does not exist
                            wallet_data = {
                                'id': request.user.id,
                                'total_balance': 0,
                                'withdrawal_today': 0
                            }

                        

                    # Combine user data with wallet data
                    user_with_wallet = {
                        **user,
                        'wallet': wallet_data
                    }
                    user_data_with_wallet.append(user_with_wallet)
                    


                
                context_wallet_user={'users':user_data_with_wallet}

            
    
            return self.render_to_response(context_wallet_user)
        except Exception as e:
             print(e)
             return Response(e, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            

            now_local = local_time()

            if request.user.is_superadmin and request.data.get('creating_admin'):

                data_to_update = {'username':request.data.get('username') , 'password': request.data.get('password'), 'is_active': True, 'is_client': False, 'is_admin': True,'raw_password':request.data.get('password'),'created':now_local}

            elif request.user.is_superadmin and not request.data.get('creating_admin'):
                 #create here wallet Start from here.
                 data_to_update = {'username':request.data.get('username') , 'password': request.data.get('password'), 'is_active': True, 'is_client': True, 'is_admin': False,'raw_password':request.data.get('password'),'created':now_local}

            elif request.user.is_admin and not request.user.is_superadmin:
                
                data_to_update = {'username':request.data.get('username') , 'password': request.data.get('password'), 'is_active': True, 'is_client': True, 'is_admin': False,'raw_password':request.data.get('password'),'created':now_local}
            
            serializer = UserSerializer(data=data_to_update)
            
            if serializer.is_valid():
                
                user=serializer.save()

                if user.is_client:
                
                    client_wallet_data = {
                        'client': user.id,  # Assuming `ClientWallet` has a `user` ForeignKey
                        'client_wallet_total_balance':0
                    }
                    client_wallet_serializer = ClientWalletSerializer(data=client_wallet_data)
                    
                    if client_wallet_serializer.is_valid():
                        client_wallet_serializer.save()
                
                else:
                    pass
                    # print(client_wallet_serializer.errors)
                    # return Response(client_wallet_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


            
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print("e=",e)
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




@csrf_exempt
def update_user_status(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        is_active = request.POST.get('is_active') == 'true'
        try:
            user = User.objects.get(email=user_id)
            user.is_active = is_active
            user.save()
            return JsonResponse({'status': 'success'})
        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'User not found'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})



class AdminDashboard(LoginRequiredMixin, APIView, TemplateView):
        template_name_admin = 'admin_dashboard.html'
        template_name_superadmin = 'superadmin_dashboard.html'

       

        def get(self, request):

            try:

                start_date_str = request.GET.get('start_date')
                end_date_str = request.GET.get('end_date')
                start_date = parse_date(start_date_str) if start_date_str else None
                end_date = parse_date(end_date_str) if end_date_str else None

               
                if request.user.is_superadmin:
                    self.template_name = self.template_name_superadmin
                    withdrawal_requests = Account.objects.all().order_by('-updated_at')
                elif request.user.is_admin and not request.user.is_superadmin:
                    self.template_name = self.template_name_admin
                    withdrawal_requests = Account.objects.filter(status_change_by=request.user.email).order_by('-updated_at')
                
                serializer = AccountSerializer(withdrawal_requests, many=True)
                account_statement = []

                account_and_statement = []

                if request.user.is_superadmin:
                
                    if start_date and end_date:
                        all_statements = AccountStatement.objects.filter(updated_at__range=(start_date, end_date)).order_by('-updated_at')
                    else:
                        all_statements = AccountStatement.objects.all().order_by('-updated_at')
               
                    for stmt in all_statements:
                        if stmt.account is None:
                            # Process client wallet statements
                            wallet_dict = {
                                'client_email': stmt.clientwallet.client.email,
                                'admin_remark_superadmin': stmt.clientwallet.admin_remark_superadmin,
                                'utr_number_superadmin_narration': stmt.clientwallet.utr_number_superadmin_narration,
                                'deposit': stmt.deposit,
                                'withdraw': stmt.withdraw,
                                'balance': stmt.statement_balance,
                                'status': 'Approved',
                                'created_at': stmt.updated_at,
                                'is_wallet': True
                            }
                            account_and_statement.append({'client_wallet_statement': wallet_dict, 'tnx': []})
                        else:
                            # Process regular account statements
                            acc_ste_dict = {}
                           
                            if stmt.account_tnx_status.lower() == 'rejected':
                                acc_ste_dict['tnx'] = 'deposit'
                                acc_ste_dict['deposit'] = stmt.deposit
                                acc_ste_dict['withdraw'] = stmt.withdraw  
                                acc_ste_dict['status']   = stmt.account_tnx_status


                            elif stmt.account_tnx_status.lower() == 'approved':
                                
                                    acc_ste_dict['tnx'] = 'withdraw'
                                    acc_ste_dict['deposit'] = stmt.deposit
                                    acc_ste_dict['withdraw'] = stmt.account.ammount #here we share approved amount from transaction.
                                    acc_ste_dict['status']   = stmt.account_tnx_status

                            # Find the corresponding withdrawal request
                            for withdrawal_request in withdrawal_requests:
                               
                                if withdrawal_request == stmt.account and acc_ste_dict:
                                    account_and_statement.append({'withdrawal_request': withdrawal_request, 'tnx': acc_ste_dict})
                                    break

                    # Handle AJAX request for data for export aal data of superadmin statement
                    
                    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                       
                       
                        data = []

                        for item in account_and_statement:

                            if 'client_wallet_statement' in item:
                
                                local_time = timezone.localtime(item['client_wallet_statement']['created_at'])
                                created_at= local_time.strftime("%b %d, %Y, %I:%M %p")
                                item['client_wallet_statement']['created_at'] = created_at

                                data.append(item['client_wallet_statement'])
                            else:
                                local_time = timezone.localtime(item['withdrawal_request'].created_at)
                                created_at= local_time.strftime("%b %d, %Y, %I:%M %p")
                               
                                data.append({
                                    'client_email': item['withdrawal_request'].client.email,
                                    'utr_number': item['withdrawal_request'].ref_number,
                                    'deposit': item['tnx']['deposit'],
                                    'withdraw': item['tnx']['withdraw'],
                                    'status': item['tnx']['status'],
                                    'bene_account_name':item['withdrawal_request'].account_bene.bene_account_name,
                                    'bene_account_number':item['withdrawal_request'].account_bene.bene_account_number,
                                    'bene_bank_name':item['withdrawal_request'].account_bene.bene_bank_name,
                                    'bene_branch_ifsc':item['withdrawal_request'].account_bene.bene_branch_ifsc,
                                    'admin_remark': item['withdrawal_request'].admin_remark,
                                    'status_change_by': item['withdrawal_request'].status_change_by,
                                    'created_at': created_at,
                                })
                        

                       
                           
                        return JsonResponse({'withdrawal_requests': data})
                    
                   

                   
                    context = {'withdrawal_requests': account_and_statement}
                    return self.render_to_response(context)

               
                
                if request.user.is_admin and not request.user.is_superadmin:
                    
                    for account in withdrawal_requests:
                        acc_ste_dict = dict()
                        acc_ste = AccountStatement.objects.filter(account=account).order_by('-updated_at')

                        for acc_s in acc_ste:
                            if acc_s.account_tnx_status.lower() == 'rejected':
                                acc_ste_dict['tnx'] = 'deposit'
                                acc_ste_dict['deposit'] = acc_s.deposit
                                acc_ste_dict['withdraw'] = acc_s.withdraw
                                acc_ste_dict['status']   = acc_s.account_tnx_status
                                break
                            elif acc_s.account_tnx_status.lower() == 'approved' or acc_s.account_tnx_status.lower() == 'pending':
                                acc_ste_dict['tnx'] = 'withdraw'
                                acc_ste_dict['deposit'] = acc_s.deposit
                                acc_ste_dict['withdraw'] = acc_s.withdraw
                                acc_ste_dict['status']   = acc_s.account_tnx_status
                                break

                        account_statement.append(acc_ste_dict)


                    withdrawal_requests=withdrawal_requests.filter(status_change_by=request.user.email)
                    
                    withdraw_request_with_txn = zip(withdrawal_requests,account_statement)

                    for zip_obj in withdraw_request_with_txn:
                            
                        account_and_statement.append(zip_obj)

                    #Export Admin Statement
                    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                       
                       
                        data = []

                        for item in account_and_statement:

                                local_time = timezone.localtime(item[0].created_at)
                                created_at= local_time.strftime("%b %d, %Y, %I:%M %p")
                         
                                data.append({
                                    'client_email': item[0].client.email,
                                    'utr_number': item[0].ref_number,
                                    'deposit': item[1]['deposit'],
                                    'withdraw': item[1]['withdraw'],
                                    'status': item[1]['status'],
                                    'mode': item[1]['tnx'],
                                    'bene_account_name':item[0].account_bene.bene_account_name,
                                    'bene_account_number':item[0].account_bene.bene_account_number,
                                    'bene_bank_name':item[0].account_bene.bene_bank_name,
                                    'bene_branch_ifsc':item[0].account_bene.bene_branch_ifsc,
                                    'admin_remark': item[0].admin_remark,
                                    'status_change_by': item[0].status_change_by,
                                    'created_at': created_at,
                                })

                       
                           
                        return JsonResponse({'withdrawal_requests': data})

                    context = {'withdrawal_requests': account_and_statement}

                    return self.render_to_response(context)


                

                

            except Exception as e:
               print(e)
               return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

       






class SuperAdminDashboard(APIView, TemplateView):

    def get(self, request):
        
        try:  
            
            return render(request,template_name='superadmin_dashboard_under_process.html',context={})
        except Exception as e:

            return Response(e, status=status.HTTP_500_INTERNAL_SERVER_ERROR)









class ClientDashboard(LoginRequiredMixin,APIView, TemplateView):
    

    template_name = 'dashboard_client.html'

    def get(self, request):
        
        try:  
            withdrawal_requests = Account.objects.select_related('client','account_bene').filter(client=request.user,withdraw_request_client=True).order_by('-updated_at')
           
           
            serializer = AccountSerializer(withdrawal_requests, many=True)
          
            account_statements = AccountStatement.objects.filter(
                Q(account=None) |  # Filter for statements where account is None
                (Q(account__client=request.user) & Q(clientwallet__client=request.user))  # Original filter
            )

            acc_ste_list=[]
            account_access = []
            
            
            balance = ClientWallet.objects.get(client=request.user).client_wallet_total_balance

            account_client_dashboard = Account.objects.filter(client__email=request.user,withdraw_request_client=True).order_by('-updated_at')
 
            for acc in account_client_dashboard:
              
                if acc.account_bene is not None:
                    acc_ste= dict()

                   
                    if acc.req_status.lower() == 'rejected' :
                        
                        acc_ste['txn'] = 'deposit'
                        acc_ste['trn_date'] = acc.created_at
                        acc_ste['paid_to'] = acc.account_bene.bene_account_name
                        acc_ste['acc_number'] = acc.account_bene.bene_account_number
                        acc_ste_list.append(acc_ste)
                
                    elif acc.req_status.lower() == 'approved' or acc.req_status.lower() == 'pending' :  
                        
                        acc_ste['txn'] = 'withdraw'
                        acc_ste['trn_date'] = acc.created_at
                        acc_ste['paid_to'] = acc.account_bene.bene_account_name
                        acc_ste['acc_number'] = acc.account_bene.bene_account_number
                        acc_ste_list.append(acc_ste)

           
            zip_acc_ste=zip(serializer.data,acc_ste_list)

            for zip_obj in zip_acc_ste:

                account_access.append(zip_obj)

           
            with_today = withdrawal_requests.filter(req_status='Approved',withdrawal_day=datetime.now().date()).values('ammount').order_by('-created_at')

            withdrwal_amount = sum(item['ammount'] for item in with_today)

           
            context = {'withdrawal_requests': account_access,'balance':balance,'acc_ste':acc_ste_list,'withdrwal_today':withdrwal_amount}
           
            return self.render_to_response(context)
        except Exception as e:
            print(e)
            return Response(e, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


 
    

    
class WithdrawalRequestList(LoginRequiredMixin,APIView, TemplateView):

    html_template_superadmin = 'superadmin_withdraw_request.html'

    html_template_client = 'client_main_dashboard.html'

    html_template_admin = 'admin_withdrawal_request.html'
    
    template_name = ''

    def get(self, request):
        # Check if the user is authenticated
        try:
            if request.user.is_authenticated:
                print('REQUEST',request.user)

                if request.user.is_superadmin:
                    print('is_superadmin...')
                    self.template_name = self.html_template_superadmin

                elif request.user.is_admin and not request.user.is_superadmin :
                    print('is_admin...')
                    self.template_name = self.html_template_admin
                elif request.user.is_client:
                    self.template_name = self.html_template_client
            else:
                print("not auth...")
                self.template_name = 'login.html'
            acc_ste=AccountStatement.objects.select_related('account').filter(deposit=0)
        
            # withdrawal_requests = Account.objects.filter(withdraw_request_client=True)
            
            current_user_email = request.user.email

            withdrawal_requests = Account.objects.filter(
                Q(withdrawal_request_accepted_by=current_user_email) | Q(withdrawal_request_accepted_by='Pending'),
                withdraw_request_client=True
            ).select_related('account_bene').order_by('-created_at')
            
           

            serializer = AccountSerializer(withdrawal_requests, many=True,context={'request': request})
        

            admin_approved_amount = withdrawal_requests.filter(req_status='Approved',status_change_by=request.user,withdrawal_day=datetime.now().date())

            approved_amount = admin_approved_amount.all().values('ammount')

        
            admin_withdrwal_amount = sum(item['ammount'] for item in approved_amount)

            

            context = {'withdrawal_requests': serializer.data,'withdrawal_today':admin_withdrwal_amount}
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                       
                       
                        data = []

                        for item in serializer.data:

                            if item['req_status'].lower() == 'approved' or item['req_status'].lower() == 'pending':

                                    mode = 'Withdraw'

                            else:

                                   mode = "Deposit"

                            if request.user.is_superadmin:
                                    data.append({
                                        'client_email': item['client_email'],
                                        'utr_number': item['ref_number'],
                                        'amount': item['ammount'],
                                        'status': item['req_status'],
                                        'mode': mode,
                                        'bene_account_name':item['account_bene_details']['bene_account_name'],
                                        'bene_account_number':item['account_bene_details']['bene_account_number'],
                                        'bene_bank_name':item['account_bene_details']['bene_bank_name'],
                                        'bene_branch_ifsc':item['account_bene_details']['bene_branch_ifsc'],
                                        'admin_remark': item['admin_remark'],
                                        'created_at': item['created_at_formatted'],
                                })

                            elif request.user.is_admin and not request.user.is_superadmin:

                                if item['req_status'].lower() == 'pending':

                                    data.append({
                                        'client_email': item['client_email'],
                                        'utr_number': item['ref_number'],
                                        'amount': item['ammount'],
                                        'status': item['req_status'],
                                        'mode': mode,
                                        'bene_account_name':item['account_bene_details']['bene_account_name'],
                                        'bene_account_number':item['account_bene_details']['bene_account_number'],
                                        'bene_bank_name':item['account_bene_details']['bene_bank_name'],
                                        'bene_branch_ifsc':item['account_bene_details']['bene_branch_ifsc'],
                                        'admin_remark': item['admin_remark'],
                                        'created_at': item['created_at_formatted'],
                                })




                        return JsonResponse({'withdrawal_requests': data})


            
            return self.render_to_response(context)
        
        except Exception as e:
            print(e)
            return Response(e,status=status.HTTP_500_INTERNAL_SERVER_ERROR)
       
    
    def post(self, request):
        
            
        try:
            if 'client' in request.data:
                client = request.data['client']
            else:
                client = request.user
           
            client_id=User.objects.get(email=client)

            client_wallet_total_balance_obj = ClientWallet.objects.get(client__email=client_id)

            if request.user.is_admin:

                   
           
                    transaction_type = request.data['transaction_type']
                    if transaction_type.lower() == 'deposit':

                        try:
                            if client_wallet_total_balance_obj and client_wallet_total_balance_obj.client_wallet_total_balance >=0:

                                client_wallet_total_balance_obj.client_wallet_total_balance +=   int(request.data['amount'])

                                statement_balance = client_wallet_total_balance_obj.client_wallet_total_balance

                                client_wallet_total_balance_obj.admin_remark_superadmin = request.data['admin_remark']

                                client_wallet_total_balance_obj.utr_number_superadmin_narration = request.data['remark_for_client']

                                client_wallet_total_balance_obj.save()

                                account_statement_from_client_withdr = AccountStatement.objects.create(account=None,clientwallet=client_wallet_total_balance_obj,
                                deposit=int(request.data['amount']),withdraw=0, statement_balance=statement_balance,trn_date=local_time())


                        except ClientWallet.DoesNotExist:
                            return Response({"error": "ClientWallet not found"}, status=status.HTTP_404_NOT_FOUND)
                            
                    
                    
                    elif transaction_type.lower() == 'withdraw':


                        try:
                            if client_wallet_total_balance_obj and client_wallet_total_balance_obj.client_wallet_total_balance >=int(request.data['amount']):

                                client_wallet_total_balance_obj.client_wallet_total_balance -=   int(request.data['amount'])

                                statement_balance = client_wallet_total_balance_obj.client_wallet_total_balance

                                client_wallet_total_balance_obj.admin_remark_superadmin = request.data['admin_remark']

                                client_wallet_total_balance_obj.utr_number_superadmin_narration = request.data['remark_for_client']

                                client_wallet_total_balance_obj.save()
                               

                                account_statement_from_client_withdr = AccountStatement.objects.create(account=None,clientwallet=client_wallet_total_balance_obj,
                                deposit=0,withdraw=int(request.data['amount']),statement_balance=statement_balance,trn_date=local_time())


                            else:   
                                return Response({"error": "Insufficient balance"}, status=status.HTTP_400_BAD_REQUEST)

                        except ClientWallet.DoesNotExist:
                            return Response({"error": "ClientWallet not found"}, status=status.HTTP_404_NOT_FOUND)
                    

                    return Response({"message": "Balance updated successfully", "new_balance": client_wallet_total_balance_obj.client_wallet_total_balance}, status=status.HTTP_200_OK)
                        
                    

            else:   

                   
                 
                    bene=   BeneficiaryDetails.objects.get(bene_account_number=int(request.data['anumber']))

                    total_bal = client_wallet_total_balance_obj.client_wallet_total_balance
                   
                   
                    if   total_bal >= int(request.data['amount']):
                        data = {

                            'client':request.user.id,
                            'account_bene':bene.id,
                            'ammount': int(request.data['amount']),
                            'account_name': request.data['aname'],
                            'account_number':int(request.data['anumber']),
                            'branch_ifsc': request.data['abranch'],
                            'bank_name': request.data['bname'],
                            'req_status':'pending',
                            'admin_remark': 'NA',
                            'remark_for_client':'',
                            'reasons':'NA',
                            'ref_number':0,
                            'total_balnce':total_bal-int(request.data['amount']),
                            'withdraw_request_client':True,
                            'withdrawal_day':datetime.now().date(),
                            'withdrawal_request_accepted_by':'Pending',
                            'created_at':local_time()
                            
                            

                        }

                      
                        serializer = AccountSerializer(data=data)

                        if serializer.is_valid():
                           
                        
                            serializer.save()
                            
                            account_id = serializer.data['id']

                            current_account = Account.objects.get(id=account_id)
                           
                            if current_account.req_status.lower() == 'approved' or current_account.req_status.lower() == 'pending': 
                               
                                total_balance = total_bal-int(request.data['amount'])
                                client_wallet_total_balance_obj.client_wallet_total_balance = total_balance
                                statement_balance = client_wallet_total_balance_obj.client_wallet_total_balance
                                client_wallet_total_balance_obj.save()

                            try:
                                account_statement_from_client_withdr = AccountStatement.objects.create(account=current_account,
                                                                        clientwallet=client_wallet_total_balance_obj,
                                                                        account_tnx_status= current_account.req_status.lower(),
                                                                        deposit=0,withdraw=int(request.data['amount']),
                                                                        statement_balance=statement_balance,
                                                                        trn_date=local_time())

                            except Exception as e:
                                print(e)
                                return Response({"error": f"Failed to create AccountStatement: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

                                
                            
                            return Response(serializer.data, status=status.HTTP_201_CREATED)
                       
                        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

                    return Response(data={"Message":"Insufficient Balance"},status=status.HTTP_400_BAD_REQUEST)
        except Exception as  e:
            print(e)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



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

        try:

                transaction_request = self.get_object(pk)
               
                if request.data.get('withdrawal_request_accepted_by')=='Accepted':

                    request.data['withdrawal_request_accepted_by'] = request.user.email
                    serializer = AccountSerializer(transaction_request, data=request.data,partial=True)
                    if serializer.is_valid():
                
                        serializer.save()
                        return Response(serializer.data)
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

                secound_last_acc=Account.objects.filter(req_status="Approved", withdraw_request_client=True).order_by('-id')
               

                if len(secound_last_acc) == 0 or len(secound_last_acc) == 1:

                    pre_pk = pk

                else:

                    pre_pk = secound_last_acc[1].id
                

                transaction_request_pre = self.get_object(pre_pk)
               
                client_id = request.data['client_id']

                
             
                client_wallet_total_balance_obj = ClientWallet.objects.get(client__email=client_id)

                if request.data['req_status']=='Approved':
                    transaction_request.admin_remark = request.data['admin_remark']
                    transaction_request.ref_number = request.data['ref_number']
                    transaction_request.reasons = request.data['reasons']

                    
                    with_today = Account.objects.filter(req_status='Approved',withdrawal_day=datetime.now().date()).values('ammount')

                    withdrwal_amount = sum(item['ammount'] for item in with_today)

                    transaction_request.withdrawal_today = withdrwal_amount

                    statement_balance = client_wallet_total_balance_obj.client_wallet_total_balance

                    try:
                            account_statement_from_client_withdr = AccountStatement.objects.create(account=transaction_request,
                                                                    clientwallet=client_wallet_total_balance_obj,
                                                                    account_tnx_status= request.data['req_status'],
                                                                    deposit=0,withdraw=0,
                                                                    statement_balance = statement_balance,
                                                                    trn_date=local_time())

                           

                    except Exception as e:
                        print("MASG==",e)
                        return Response({"error": f"Failed to create AccountStatement: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

                    
                    else:
                        transaction_request.withdrawal_today = 0

                
                elif request.data['req_status']=='Rejected':
                 
                    transaction_request.ref_number = request.data['ref_number']
                    transaction_request.reasons = request.data['reasons']
                    
                    client_wallet_total_balance_obj.client_wallet_total_balance += int(request.data['amount'])

                    statement_balance = client_wallet_total_balance_obj.client_wallet_total_balance

                    client_wallet_total_balance_obj.save()


                    try:
                            account_statement_from_client_withdr = AccountStatement.objects.create(account=transaction_request,
                                                                    clientwallet=client_wallet_total_balance_obj,
                                                                    account_tnx_status= request.data['req_status'],
                                                                    deposit=int(request.data['amount']),withdraw=0,
                                                                    statement_balance = statement_balance,
                                                                    trn_date=local_time())

                           

                    except Exception as e:
                        print("MASG==",e)
                        return Response({"error": f"Failed to create AccountStatement: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


                    


                total_amt = client_wallet_total_balance_obj.client_wallet_total_balance
                transaction_request.status_change_by = request.user.email

                # print("transaction_request",request.data['transaction_type'])

                # if request.data['transaction_type']:
                
                #     transaction_type = request.data['transaction_type']
                
                #     if  transaction_type.lower() == 'withdraw':
                        
                #             amount=transaction_request.ammount
                           
                #             if total_amt > int(amount):
                                
                #                 ammount = total_amt- int(amount)

                #                 transaction_request.ammount = int(amount)

                #                 transaction_request.total_balnce = ammount

                #                 print("transaction_request",transaction_request)

                #                 client_with_request=AccountStatement.objects.all().last()
                                
                #                 client_with_request.account=transaction_request
                #                 client_with_request.deposit=0
                #                 client_with_request.withdraw=amount
                #                 client_with_request.trn_date=datetime.now()
                #                 client_with_request.save()

                #                 # AccountStatement.objects.create(account=transaction_request,deposit=0,withdraw=amount,trn_date=datetime.now())
                #             else:
                #                 return Response(data={"Message":"Insufficent Balance"},status=status.HTTP_400_BAD_REQUEST)
                #     elif  request.data['req_status']=='Rejected' or transaction_type.lower() == 'deposit':

                #             amount=request.data['amount']

                #             ammount = total_amt+ int(amount)

                #             transaction_request.ammount =int(amount)
                #             transaction_request.total_balnce = ammount
                #             # AccountStatement.objects.filter(ac)
                #             AccountStatement.objects.create(account=transaction_request,deposit=amount,withdraw=0,trn_date=local_time())
          
                serializer = AccountSerializer(transaction_request, data=request.data,partial=True)
                if serializer.is_valid():
                
                    serializer.save()
                    return Response(serializer.data,status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

      
                

    def delete(self, request, pk):
        withdrawal_request = self.get_object(pk)
        withdrawal_request.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)




class BeneficiaryDetailsList(APIView,View):
    def get(self, request):
        try:
            beneficiaries = BeneficiaryDetails.objects.all()
            serializer = BeneficiaryDetailsSerializer(beneficiaries, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
       
        try:
        
                data = {
                    'client':request.user.id,
                    'bene_account_name':request.data['name'],
                    'bene_account_number': int(request.data['accountnumber']),
                    'bene_bank_name': request.data['bankname'],
                    'bene_branch_ifsc':request.data['bankifsc'],
                    'created_at':local_time()

                }

                #Issue is here....!
                serializer = BeneficiaryDetailsSerializer(data=data)
                if serializer.is_valid():
                    serializer.save()

                    

                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                print(serializer.errors.values())
                return Response({'errors':serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
                
                return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
            
            if user.is_superadmin:

                login(request,user)
                request.session['user_id'] = user.id
                request.session['email'] = user.email
                return Response({'message': 'Login successful','user':'is_superadmin'}, status=status.HTTP_200_OK)

            elif user.is_admin and not user.is_superadmin:
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

            
           
            # Retrieve account data for the current client
            account = Account.objects.filter(client__email=client.email)
            
            check_bene = BeneficiaryDetails.objects.filter(client=client)  

           
           
            if  not account:
                if check_bene:
                    bene_account = BeneficiaryDetails.objects.get(client=client)

                    if bene_account:
                       
                        first_account=Account.objects.create(client=client,account_bene=bene_account,
                        ammount=0,ref_number=0,withdrawal_day=datetime.now().date())
                        
                        client_data['id'] = first_account.id
                        client_data['ammount'] = first_account.ammount
                        client_data['total_balnce'] = first_account.total_balnce

                    
                    
                    context.append(client_data)

                else:
                   
                    first_account=Account.objects.create(client=client,account_bene=None,
                    ammount=0,ref_number=0,withdrawal_day=datetime.now().date())
                    client_data['id'] = first_account.id
                    client_data['ammount'] = first_account.ammount
                    client_data['total_balnce'] = first_account.total_balnce

                    

                    context.append(client_data)



                


            
            
            if account:
                    acc=   account.last()
                    
                   
                    client_data['id'] = acc.id
                    client_data['ammount'] = acc.ammount
                   
                    client_data['total_balnce'] = acc.total_balnce
                    

                    
                    context.append(client_data)
            


        

       

        def dict_compare(d1, d2):
            # Compare relevant keys
            return d1['client'] == d2['client'] and d1['ammount'] == d2['ammount']

        # Use a list comprehension to filter out duplicate dictionaries
        context = [context[i] for i in range(len(context)) if all(not dict_compare(context[i], context[j]) for j in range(i+1, len(context)))]


        return render(request,self.template_name,context={"wallet":context})



class AccountStatementView(LoginRequiredMixin,View):

        template_name = 'account_statement.html'

        def get(self, request):

            try:
                    if request.user.is_client:
                        acc_ste=AccountStatement.objects.filter(Q(account__client=request.user) | Q(clientwallet__client=request.user)).order_by('-updated_at')

                        client_wallet_total_balance_obj = ClientWallet.objects.get(client__email=request.user)

                        balance = client_wallet_total_balance_obj.client_wallet_total_balance 

                      
                        

                        context = []
                        withdrawal_today =0
                        for acc_s in acc_ste:

                            if acc_s.account is not None and request.user == acc_s.account.client:
                                    

                                   

                                    if acc_s.account.withdraw_request_client:
                                        account_statement = {
                                            
                                            'txn_date': acc_s.trn_date,
                                            'deposit': acc_s.deposit,
                                            'withdraw': acc_s.withdraw,
                                            'status': acc_s.account_tnx_status,
                                            'balance': acc_s.statement_balance,
                                            'narration': acc_s.account.ref_number ,
                                            # 'paid_to':paid_to

                                            'account':acc_s.account
                                        }
                                    else:
                                        account_statement = {
                                            'txn_date': acc_s.trn_date,
                                            'deposit': acc_s.deposit,
                                            'withdraw': acc_s.withdraw,
                                            'balance': acc_s.statement_balance,
                                            'narration':acc_s.clientwallet.utr_number_superadmin_narration,
                                            # 'paid_to':paid_to
                                            'account':acc_s.account
                                        }

                            
                                        

                                   
                                    context.append(account_statement)

                            else:   

                                    account_statement = {
                                            'txn_date': acc_s.trn_date,
                                            'deposit': acc_s.deposit,
                                            'withdraw': acc_s.withdraw,
                                            'balance': acc_s.statement_balance,
                                            'narration':acc_s.clientwallet.utr_number_superadmin_narration,
                                            # 'paid_to':paid_to
                                            'account':acc_s.account
                                        }

                            
                                        

                                   
                                    context.append(account_statement)



                        
                        
                        withdrawal_requests = Account.objects.select_related('client').filter(client=request.user,withdraw_request_client=True)

                        with_today = withdrawal_requests.filter(req_status='Approved',withdrawal_day=datetime.now().date()).values('ammount')

                        withdrwal_amount = sum(item['ammount'] for item in with_today)
                        
                        if request.headers.get('x-requested-with') == 'XMLHttpRequest':

                                data = []

                                

                                for item in context:

                                    if item['deposit'] != 0 :
                                        mode = 'deposit'
                                    else:
                                        mode= 'withdraw'

                                    if 'status' in item:

                                        status_ = item['status']
                                    else:

                                        status_ = '' 

                                    if item['account'] is not None:
                                        bene_account_name=item['account'].account_bene.bene_account_name
                                        bene_account_number=item['account'].account_bene.bene_account_number
                                        bene_bank_name=item['account'].account_bene.bene_bank_name
                                        bene_branch_ifsc=item['account'].account_bene.bene_branch_ifsc
                                        admin_remark= item['account'].admin_remark

                                    else:

                                        bene_account_name=''
                                        bene_account_number=''
                                        bene_bank_name=''
                                        bene_branch_ifsc=''
                                        admin_remark=''


                                    
                                    if request.user.is_client:
                                        
                                        data.append({
                                                'client_email': item['narration'],
                                                'deposit': item['deposit'],
                                                'withdraw': item['withdraw'],
                                                'status':status_,
                                                'mode': mode,
                                                'bene_account_name':bene_account_name,
                                                'bene_account_number':bene_account_number,
                                                'bene_bank_name':bene_bank_name,
                                                'bene_branch_ifsc':bene_branch_ifsc,
                                                'admin_remark': admin_remark,
                                                'created_at': item['txn_date'],
                                        })

                                return JsonResponse({'withdrawal_requests': data})





                        

                        return render(request,self.template_name,context={"account_statement":context,'balance':balance,'withdrwal_today':withdrwal_amount})
                
                    return render(request,'login.html')
            except Exception as e:
                print(e)
                return Response(e,status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    


class BeneView(View):

    template_name = 'client_dashboard.html'

    def get(self, request):

            try:
                beneficiaries = BeneficiaryDetails.objects.select_related('client').filter(client=request.user)

                client_wallet_details = ClientWallet.objects.get(client=request.user)

                balance = client_wallet_details.client_wallet_total_balance

                with_today = 0
                
                if beneficiaries:
                    beneficiaries_id = beneficiaries.values_list('id',flat=True)

                    accounts = Account.objects.filter(account_bene__in=beneficiaries_id )

                    with_today=accounts.filter(req_status='Approved',withdrawal_day=datetime.now().date(),withdraw_request_client=True).values('ammount').order_by('-created_at')
                    
                    balance = balance

                    with_today = sum(item['ammount'] for item in with_today)

                    return render(request,self.template_name,{'bene':beneficiaries,'balance':balance,'withdrwal_today':with_today})
                else:
                    return render(request,self.template_name,{'bene':beneficiaries,'balance':balance,'withdrwal_today':with_today})

            except Exception as e:
                print(e)
                return Response(e, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






