from django.contrib import admin
from django.urls import path,include
from .views import *
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    path('', TemplateView.as_view(template_name='login.html'), name='login'),

    path('userlogin/', UserLogin.as_view(), name='user-login'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),

    path('users/', UserList.as_view(), name='user-list'),
    path('users/<int:pk>/', UserDetail.as_view(), name='user-detail'),

    # Admin
    path('users/template/', TemplateView.as_view(template_name='client.html'), name='client-list-template'),

    path('users/admintemplate/', TemplateView.as_view(template_name='admin.html'), name='admin-list-template'),

    path('admin_dashboard/template/', AdminDashboard.as_view(template_name='admin_dashboard.html'), name='admin_dashboard'),
    
    #Client

    path('dashboard_client/template/', ClientDashboard.as_view(template_name='dashboard_client.html'), name='dashboard-client-form'),


    path('beneficiaries/', BeneficiaryDetailsList.as_view(), name='beneficiary-list'),
    path('beneficiaries/<int:pk>/', BeneficiaryDetailsDetail.as_view(), name='beneficiary-detail'),
    path('add_bene/template/', TemplateView.as_view(template_name='add_bene.html'), name='add-bene-template'),


    path('withdrawal-requests/', WithdrawalRequestList.as_view(), name='withdrawal-request-list'),
    path('withdrawal-requests/<int:pk>/', WithdrawalRequestDetail.as_view(), name='withdrawal-request-detail'),
    path('withdrawal-requests/template/', BeneView.as_view(), name='withdrawal-requests-template'),

    


    path('client_wallet_list/template/', WalletListView.as_view(),name='client_wallet_list'),
    path('account_statement/template/',AccountStatementView.as_view(),name='account_statement_list'),

    # path('bene_table/template/',BeneView.as_view(),name='bene-table-list'),

]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
