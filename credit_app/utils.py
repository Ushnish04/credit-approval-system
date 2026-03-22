import math
import datetime


def calculate_monthly_installment(loan_amount: float, interest_rate: float, tenure: int) -> float:
    """
    EMI formula using compound interest:
    EMI = P * r * (1+r)^n / ((1+r)^n - 1)
    P = principal, r = monthly rate, n = tenure in months
    """
    if interest_rate == 0:
        return round(loan_amount / tenure, 2) if tenure > 0 else 0

    r = interest_rate / (12 * 100)
    n = tenure
    emi = loan_amount * r * math.pow(1 + r, n) / (math.pow(1 + r, n) - 1)
    return round(emi, 2)


def calculate_credit_score(customer) -> int:
    loans = list(customer.loans.all())
    current_year = datetime.date.today().year

    # Rule: if current loans > approved limit, score = 0
    current_loans = [l for l in loans if l.is_active]
    sum_current_loans = sum(l.loan_amount for l in current_loans)
    if sum_current_loans > customer.approved_limit:
        return 0

    if not loans:
        return 50

    # Component 1: EMIs paid on time (35 pts)
    total_emis = sum(l.tenure for l in loans)
    emis_on_time = sum(l.emis_paid_on_time for l in loans)
    on_time_ratio = emis_on_time / total_emis if total_emis > 0 else 0
    component_1 = on_time_ratio * 35

    # Component 2: Number of loans (20 pts)
    num_loans = len(loans)
    if num_loans <= 2:
        component_2 = 20
    elif num_loans <= 5:
        component_2 = 15
    elif num_loans <= 10:
        component_2 = 10
    else:
        component_2 = 5

    # Component 3: Loan activity this year (20 pts)
    current_year_loans = [l for l in loans if l.start_date and l.start_date.year == current_year]
    num_this_year = len(current_year_loans)
    if num_this_year == 0:
        component_3 = 20
    elif num_this_year <= 2:
        component_3 = 15
    elif num_this_year <= 4:
        component_3 = 10
    else:
        component_3 = 5

    # Component 4: Loan volume vs approved limit (25 pts)
    total_volume = sum(l.loan_amount for l in loans)
    volume_ratio = total_volume / customer.approved_limit if customer.approved_limit > 0 else 1
    if volume_ratio <= 0.5:
        component_4 = 25
    elif volume_ratio <= 1.0:
        component_4 = 20
    elif volume_ratio <= 2.0:
        component_4 = 10
    else:
        component_4 = 5

    score = int(component_1 + component_2 + component_3 + component_4)
    return min(100, max(0, score))


def check_loan_approval(customer, loan_amount: float, interest_rate: float, tenure: int):
    """
    Returns (approval, corrected_interest_rate, monthly_installment, message)
    """
    import datetime
    today = datetime.date.today()

    # Check: current EMIs > 50% of monthly salary
    current_loans = customer.loans.filter(end_date__gte=today) | customer.loans.filter(end_date__isnull=True)
    current_loans = current_loans.distinct()
    sum_current_emis = sum(l.monthly_repayment for l in current_loans)

    if sum_current_emis > 0.5 * customer.monthly_salary:
        emi = calculate_monthly_installment(loan_amount, interest_rate, tenure)
        return False, interest_rate, emi, "Current EMIs exceed 50% of monthly salary"

    credit_score = calculate_credit_score(customer)

    # Determine minimum rate based on credit score
    if credit_score > 50:
        min_rate = 0
    elif 30 < credit_score <= 50:
        min_rate = 12
    elif 10 < credit_score <= 30:
        min_rate = 16
    else:
        emi = calculate_monthly_installment(loan_amount, interest_rate, tenure)
        return False, interest_rate, emi, "Credit score too low"

    corrected_rate = max(interest_rate, min_rate)
    monthly_installment = calculate_monthly_installment(loan_amount, corrected_rate, tenure)
    approved = interest_rate >= min_rate

    if not approved:
        return False, corrected_rate, monthly_installment, f"Interest rate corrected to minimum {min_rate}%"

    return True, corrected_rate, monthly_installment, ""