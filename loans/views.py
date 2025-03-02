from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import CreateAPIView ,ListAPIView
from .serializers import *
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, permission_classes
from django.core.mail import send_mail
from .models import OTP
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from decimal import Decimal
from django.shortcuts import get_object_or_404
from datetime import timedelta
from django.utils import timezone




# Create your views here.

#user registration view

User = get_user_model()

class UserRegistrationView(APIView):
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.is_active = False  # Deactivate user until OTP is verified
            user.save()

            # Delete previous OTPs for this user
            OTP.objects.filter(user=user).delete()

            # Generate a random 6-digit OTP
            otp_code = str(random.randint(100000, 999999))

            # Store OTP in the database
            OTP.objects.create(user=user, otp_code=otp_code)

            # Send OTP to user's email
            send_mail(
                "Your OTP Code",
                f"Your OTP code is {otp_code}",
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )

            return Response(
                {"message": "User created successfully! Please verify OTP."},
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#user login

@csrf_exempt  # ✅ Disables CSRF check for this view
def custom_login(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST requests allowed"}, status=405)

    try:
        data = json.loads(request.body)  # ✅ Parse JSON manually
        username = data.get("username")
        password = data.get("password")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    user = authenticate(username=username, password=password)

    if user is not None:
        refresh = RefreshToken.for_user(user)
        role = "admin" if user.is_staff else "user"  # ✅ Identify user role

        return JsonResponse({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "role": role,
            "message": "Login successful!"
        }, status=200)
    else:
        return JsonResponse({"error": "Invalid credentials"}, status=400)






#verify otp

User = get_user_model()

@api_view(['POST'])
def verify_otp(request):
    email = request.data.get('email')
    otp_code = str(request.data.get('otp'))  # Convert OTP to string

    user = User.objects.filter(email=email).first()
    if not user:
        return Response({'error': 'User not found'}, status=400)

    try:
        # Fetch the latest OTP entry for the user
        otp = OTP.objects.filter(user=user).latest('created_at')

        # Validate OTP
        if otp.otp_code != otp_code:
            return Response({'error': 'Invalid OTP'}, status=400)

        # Activate the user
        user.is_active = True
        user.save()

        # Delete OTP after successful verification
        otp.delete()

        return Response({'message': 'OTP verified, registration complete!'}, status=200)

    except OTP.DoesNotExist:
        return Response({'error': 'Invalid OTP'}, status=400)

#Loan creation view

class LoanCreateView(CreateAPIView):
    serializer_class = LoanSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            loan = serializer.save(user=request.user)  # Save the loan with the user
            response_data = {
                "status": "success",
                "data": {
                    "loan_id": f"LOAN{loan.id:03d}",
                    "amount": loan.amount,
                    "tenure": loan.tenure,
                    "interest_rate": f"{loan.interest_rate}% yearly",
                    "monthly_installment": serializer.get_monthly_installment(loan),
                    "total_interest": serializer.get_total_interest(loan),
                    "total_amount": serializer.get_total_amount(loan),
                    "payment_schedule": serializer.get_payment_schedule(loan)
                }
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#Loan list view

class LoanListView(ListAPIView):
    """
    API to list all loans of the authenticated user.
    """
    serializer_class = LoanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Loan.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serialized_data = []

        for loan in queryset:
            serializer = self.get_serializer(loan)
            loan_data = serializer.data

            # Calculate amount paid and amount remaining
            total_paid_installments = max(0, (timezone.now().date() - loan.created_at.date()).days // 30)
            amount_paid = round(total_paid_installments * loan_data["monthly_installment"], 2)
            amount_remaining = round(loan_data["total_amount"] - amount_paid, 2)

            # Calculate next due date
            next_due_date = loan.created_at.date() + timedelta(days=30 * (total_paid_installments + 1))

            loan_data.update({
                "amount_paid": amount_paid,
                "amount_remaining": amount_remaining,
                "next_due_date": next_due_date.isoformat()
            })
            serialized_data.append(loan_data)

        return Response({"status": "success", "data": {"loans": serialized_data}})


#Loan Foreclosure

class LoanForeclosureView(APIView):
    def post(self, request, loan_id):
        serializer = LoanForeclosureSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({"status": "error", "errors": serializer.errors}, status=400)

        loan = serializer.validated_data["loan_id"]  # Loan object

        total_amount_due = loan.get_total_amount()
        amount_paid = loan.get_amount_paid()
        amount_remaining = total_amount_due - amount_paid

        # Fix: Ensure we use Decimal
        foreclosure_discount = amount_remaining * Decimal("0.05")
        final_settlement_amount = amount_remaining - foreclosure_discount

        # Ensure loan is only closed if final settlement is paid**
        if final_settlement_amount > 0:
            return Response({
                "status": "error",
                "message": "Loan cannot be foreclosed. Please pay the full final settlement amount.",
                "data": {
                    "loan_id": f"LOAN{loan.id:03d}",
                    "amount_paid": float(amount_paid),
                    "foreclosure_discount": round(float(foreclosure_discount), 2),
                    "final_settlement_amount": round(float(final_settlement_amount), 2),
                    "status": "ACTIVE"  # Loan remains active
                }
            }, status=400)

        # If fully paid, mark as CLOSED
        loan.status = "CLOSED"
        loan.save()

        response_data = {
            "status": "success",
            "message": "Loan foreclosed successfully.",
            "data": {
                "loan_id": f"LOAN{loan.id:03d}",
                "amount_paid": float(amount_paid),
                "foreclosure_discount": round(float(foreclosure_discount), 2),
                "final_settlement_amount": round(float(final_settlement_amount), 2),
                "status": "CLOSED"
            }
        }

        return Response(response_data, status=200)

#Admin registration View

User = get_user_model()

class AdminRegisterView(APIView):
    """
    Admin Registration View
    """
    def post(self, request):
        serializer = AdminRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    "status": "success",
                    "message": "Admin registered successfully",
                    "data": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "role": user.role,
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        return Response({"status": "error", "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

#Admin login view

User = get_user_model()

class AdminLoginView(APIView):
    """
     Admin Login with Email and Password
    """
    def post(self, request):
        serializer = AdminLoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            password = serializer.validated_data["password"]

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({"status": "error", "message": "Invalid email"}, status=400)

            user = authenticate(username=user.username, password=password)  # ✅ Authenticate using username

            if user and user.role == "admin":
                refresh = RefreshToken.for_user(user)
                return Response({
                    "status": "success",
                    "message": "Admin logged in successfully",
                    "access_token": str(refresh.access_token),
                    "refresh_token": str(refresh),
                    "role": user.role
                }, status=200)

        return Response({"status": "error", "message": "Invalid credentials or not an admin"}, status=401)

#Admin Loan List view

class AdminLoanListView(ListAPIView):
    serializer_class = LoanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin():  #  Admins see all loans
            return Loan.objects.all()
        return Loan.objects.filter(user=user)  # Regular users see only their own

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serialized_data = LoanSerializer(queryset, many=True).data
        return Response({"status": "success", "data": {"loans": serialized_data}})


#Admin Loan Deatil view

class AdminUserLoanDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        if not request.user.is_admin():
            return Response({"error": "Permission denied"}, status=403)

        loans = Loan.objects.filter(user_id=user_id)
        if not loans.exists():
            return Response({"error": "No loans found for this user"}, status=404)

        serialized_loans = LoanSerializer(loans, many=True).data
        return Response({"status": "success", "data": {"user_loans": serialized_loans}})

#Admin Loan Delete view

class AdminLoanDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, loan_id):
        if not request.user.is_admin():
            return Response({"error": "Permission denied"}, status=403)

        loan = get_object_or_404(Loan, id=loan_id)
        loan.delete()
        return Response({"message": "Loan deleted successfully"}, status=200)

