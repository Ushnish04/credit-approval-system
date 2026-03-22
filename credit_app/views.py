import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Customer, Loan
from .serializers import (
    CustomerRegisterSerializer,
    CheckEligibilitySerializer,
    CreateLoanSerializer,
)
from .utils import calculate_monthly_installment, check_loan_approval


class RegisterView(APIView):

    def post(self, request):
        serializer = CustomerRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        monthly_income = data['monthly_income']

        # approved_limit = 36 * salary, rounded to nearest lakh
        raw_limit = 36 * monthly_income
        approved_limit = round(raw_limit / 100000) * 100000

        customer = Customer.objects.create(
            first_name=data['first_name'],
            last_name=data['last_name'],
            age=data['age'],
            phone_number=data['phone_number'],
            monthly_salary=monthly_income,
            approved_limit=approved_limit,
            current_debt=0,
        )

        return Response({
            'customer_id': customer.customer_id,
            'name': f"{customer.first_name} {customer.last_name}",
            'age': customer.age,
            'monthly_income': customer.monthly_salary,
            'approved_limit': customer.approved_limit,
            'phone_number': customer.phone_number,
        }, status=status.HTTP_201_CREATED)


class CheckEligibilityView(APIView):

    def post(self, request):
        serializer = CheckEligibilitySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            customer = Customer.objects.get(customer_id=data['customer_id'])
        except Customer.DoesNotExist:
            return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)

        approval, corrected_rate, monthly_installment, message = check_loan_approval(
            customer,
            data['loan_amount'],
            data['interest_rate'],
            data['tenure'],
        )

        return Response({
            'customer_id': customer.customer_id,
            'approval': approval,
            'interest_rate': data['interest_rate'],
            'corrected_interest_rate': corrected_rate,
            'tenure': data['tenure'],
            'monthly_installment': monthly_installment,
        })


class CreateLoanView(APIView):

    def post(self, request):
        serializer = CreateLoanSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            customer = Customer.objects.get(customer_id=data['customer_id'])
        except Customer.DoesNotExist:
            return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)

        approval, corrected_rate, monthly_installment, message = check_loan_approval(
            customer,
            data['loan_amount'],
            data['interest_rate'],
            data['tenure'],
        )

        if not approval:
            return Response({
                'loan_id': None,
                'customer_id': customer.customer_id,
                'loan_approved': False,
                'message': message,
                'monthly_installment': monthly_installment,
            })

        # Calculate end date from tenure
        start_date = datetime.date.today()
        month = start_date.month - 1 + data['tenure']
        year = start_date.year + month // 12
        month = month % 12 + 1
        end_date = datetime.date(year, month, start_date.day)

        loan = Loan.objects.create(
            customer=customer,
            loan_amount=data['loan_amount'],
            tenure=data['tenure'],
            interest_rate=corrected_rate,
            monthly_repayment=monthly_installment,
            emis_paid_on_time=0,
            start_date=start_date,
            end_date=end_date,
        )

        return Response({
            'loan_id': loan.loan_id,
            'customer_id': customer.customer_id,
            'loan_approved': True,
            'message': 'Loan approved successfully',
            'monthly_installment': monthly_installment,
        }, status=status.HTTP_201_CREATED)


class ViewLoanView(APIView):

    def get(self, request, loan_id):
        try:
            loan = Loan.objects.select_related('customer').get(loan_id=loan_id)
        except Loan.DoesNotExist:
            return Response({'error': 'Loan not found'}, status=status.HTTP_404_NOT_FOUND)

        customer = loan.customer
        return Response({
            'loan_id': loan.loan_id,
            'customer': {
                'id': customer.customer_id,
                'first_name': customer.first_name,
                'last_name': customer.last_name,
                'phone_number': customer.phone_number,
                'age': customer.age,
            },
            'loan_amount': loan.loan_amount,
            'interest_rate': loan.interest_rate,
            'monthly_installment': loan.monthly_repayment,
            'tenure': loan.tenure,
        })


class ViewLoansView(APIView):

    def get(self, request, customer_id):
        try:
            customer = Customer.objects.get(customer_id=customer_id)
        except Customer.DoesNotExist:
            return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)

        loans = customer.loans.all()
        result = []
        for loan in loans:
            result.append({
                'loan_id': loan.loan_id,
                'loan_amount': loan.loan_amount,
                'interest_rate': loan.interest_rate,
                'monthly_installment': loan.monthly_repayment,
                'repayments_left': loan.repayments_left,
            })

        return Response(result)
