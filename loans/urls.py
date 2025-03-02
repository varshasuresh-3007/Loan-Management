from django.urls import path
from .views import *

urlpatterns = [
    # User Authentication
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('verify-otp/', verify_otp, name='verify-otp'),
    path('login/', custom_login, name='custom_login'),
   # Loan Management
    path('loans/', LoanCreateView.as_view(), name='loan-list'),
    path('loanslist/', LoanListView.as_view(), name='loan-list'),
    path('loans/<str:loan_id>/foreclose/', LoanForeclosureView.as_view(), name='loan-foreclose'),
    # Admin Authentication
    path("admin/register/", AdminRegisterView.as_view(), name="admin-register"), #Admin registration
    path("admin/login/", AdminLoginView.as_view(), name="admin-login"), #Admin login
    # Admin Loan Management
    path('admin/loans/', AdminLoanListView.as_view(), name='admin-loan-list'),  # View all loans
    path('admin/loans/<int:user_id>/', AdminUserLoanDetailView.as_view(), name='admin-user-loans'),  # View loans of a specific user
    path('admin/loans/<int:loan_id>/delete/', AdminLoanDeleteView.as_view(), name='admin-loan-delete'),  # Delete a loan
]
