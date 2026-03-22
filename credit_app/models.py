from django.db import models
import datetime

class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    age = models.IntegerField(null=True, blank=True)
    phone_number = models.BigIntegerField()
    monthly_salary = models.IntegerField()
    approved_limit = models.IntegerField()
    current_debt = models.FloatField(default=0)

    class Meta:
        db_table = 'customers'


class Loan(models.Model):
    loan_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='loans')
    loan_amount = models.FloatField()
    tenure = models.IntegerField()
    interest_rate = models.FloatField()
    monthly_repayment = models.FloatField()
    emis_paid_on_time = models.IntegerField(default=0)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'loans'

    @property
    def is_active(self):
        today = datetime.date.today()
        if self.end_date is None:
            return True
        return self.end_date >= today

    @property
    def repayments_left(self):
        today = datetime.date.today()
        if self.end_date is None or self.start_date is None:
            return self.tenure
        if today >= self.end_date:
            return 0
        elapsed = (today.year - self.start_date.year) * 12 + (today.month - self.start_date.month)
        return max(0, self.tenure - elapsed)