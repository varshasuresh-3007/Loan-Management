from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models
from decimal import Decimal
from django.contrib.auth.models import User
import random

# Create your models here.


# class CustomUser(AbstractUser):
#     email = models.EmailField(unique=True, blank=False, null=False)  # ✅ Ensures no NULL values
#     ROLE_CHOICES = (
#         ('admin', 'Admin'),
#         ('user', 'User'),
#     )
#     role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
#
#     def __str__(self):
#         return self.email

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True, blank=False, null=False)  # ✅ Ensure email is required and unique
    ROLE_CHOICES = (
        ('user', 'User'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')

    def is_admin(self):
        return self.role == "admin"

    def __str__(self):
        return self.username





class OTP(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Correct reference
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"OTP for {self.user}"




class Loan(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('CLOSED', 'Closed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    tenure = models.IntegerField(help_text="Loan tenure in months")
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)

    def calculate_foreclosure(self):
        """
        Calculate foreclosure discount and final settlement amount.
        """
        amount_paid = self.get_amount_paid()
        total_amount_due = self.get_total_amount()  # ✅ Corrected here
        remaining_amount = total_amount_due - amount_paid
        foreclosure_discount = remaining_amount * 0.05  # 5% discount on remaining balance
        final_settlement_amount = remaining_amount - foreclosure_discount
        return amount_paid, foreclosure_discount, final_settlement_amount

    def get_amount_paid(self):
        """
        Calculate the total amount paid so far.
        """
        return round(self.get_monthly_installment() * 2, 2)  # Assuming 2 months paid

    def get_monthly_installment(self):
        r = self.interest_rate / 100 / 12  # Convert annual rate to monthly
        emi = (self.amount * r * ((1 + r) ** self.tenure)) / (((1 + r) ** self.tenure) - 1)
        return round(emi, 2)

    def get_total_amount(self):
        return round(self.get_monthly_installment() * self.tenure, 2)

    def foreclose_loan(self):
        """
        Mark loan as foreclosed.
        """
        self.status = "CLOSED"
        self.save()


