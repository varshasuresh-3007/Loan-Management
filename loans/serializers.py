from rest_framework import serializers
from .models import *
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate



User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'role']  # Ensure 'email' is included
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = CustomUser.objects.create_user(**validated_data)
        return user

class OTPSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTP
        fields = ['user', 'otp_code']  # Ensure field name matches the model

class LoanSerializer(serializers.ModelSerializer):
    loan_id = serializers.SerializerMethodField()
    monthly_installment = serializers.SerializerMethodField()
    total_interest = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()
    payment_schedule = serializers.SerializerMethodField()

    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    tenure = serializers.IntegerField(required=True)
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2, required=True)

    class Meta:
        user_id = serializers.ReadOnlyField(source="user.id")
        model = Loan
        fields = ['user_id','loan_id', 'amount', 'tenure', 'interest_rate', 'monthly_installment',
                  'total_interest', 'total_amount', 'status', 'created_at', 'payment_schedule',]

    def validate_amount(self, value):
        if value < 1000 or value > 100000:
            raise serializers.ValidationError("Loan amount must be between ₹1,000 and ₹100,000.")
        return value

    def validate_tenure(self, value):
        if value < 3 or value > 24:
            raise serializers.ValidationError("Loan tenure must be between 3 to 24 months.")
        return value

    def get_loan_id(self, obj):
        return f"LOAN{obj.id:03d}"

    def get_monthly_installment(self, obj):
        r = obj.interest_rate / 100 / 12  # Convert annual rate to monthly
        emi = (obj.amount * r * ((1 + r) ** obj.tenure)) / (((1 + r) ** obj.tenure) - 1)
        return round(emi, 2)

    def get_total_interest(self, obj):
        total_payment = self.get_monthly_installment(obj) * obj.tenure
        return round(total_payment - obj.amount, 2)

    def get_total_amount(self, obj):
        return round(self.get_monthly_installment(obj) * obj.tenure, 2)

    def get_payment_schedule(self, obj):
        from datetime import timedelta
        from django.utils import timezone

        schedule = []
        monthly_due = self.get_monthly_installment(obj)
        due_date = timezone.now().date()

        for i in range(1, obj.tenure + 1):
            schedule.append({
                "installment_no": i,
                "due_date": (due_date + timedelta(days=30 * i)).isoformat(),
                "amount": monthly_due
            })
        return schedule


class LoanForeclosureSerializer(serializers.Serializer):
    loan_id = serializers.CharField()

    def validate_loan_id(self, value):
        try:
            loan_id = int(value.replace("LOAN", ""))  # Extract numeric ID
            loan = Loan.objects.get(id=loan_id)
        except (ValueError, Loan.DoesNotExist):
            raise serializers.ValidationError("Loan not found.")

        if loan.status == "CLOSED":
            raise serializers.ValidationError("Loan is already closed.")

        return loan  # Return the Loan object, not just the ID

User = get_user_model()

class AdminRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "role"]
        extra_kwargs = {
            "role": {"required": False, "default": "admin"},
        }

    def create(self, validated_data):
        validated_data["role"] = "admin"  # ✅ Force role to be "admin"
        user = User.objects.create_user(**validated_data)  # Django’s built-in create_user method
        return user



class AdminLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


