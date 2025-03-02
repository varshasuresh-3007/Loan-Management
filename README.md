# Loan Management System API

A Django-based Loan Management System that allows users to apply for loans, track loan status, make payments, and foreclose loans.

##  Features
- User Authentication (JWT)
- Loan Application & Approval System
- Installment Calculation & Payment Tracking
- Loan Foreclosure with Discount Calculation
- Admin Panel for Loan Management

---

##  Installation Guide

### **1. Clone the Repository**
```bash
git clone https://github.com/varshasuresh-3007/Loan-Management.git
cd Loan-Management

## **2.Create a Virtual Environment & Install Dependencies
python -m venv venv
source venv/bin/activate  # On Mac/Linux
venv\Scripts\activate  # On Windows
pip install -r requirements.txt

## **3.Set Up Environment Variables
Rename .env.example to .env and update values:
SECRET_KEY=your_secret_key
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_email_password

## **4.Run Migrations & Start Server
python manage.py migrate
python manage.py runserver

## **5.Importing Postman Collection 
