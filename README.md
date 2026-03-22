# Credit Approval System

A backend system for managing credit approvals built with Django, Celery, PostgreSQL and Redis — fully dockerized.

## Tech Stack

- **Django 5.2** + Django REST Framework
- **PostgreSQL** — database
- **Celery** + **Redis** — background task queue for data ingestion
- **Docker** + **Docker Compose** — containerization

## Project Structure
```
credit_system/
├── manage.py
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
├── celery_entrypoint.sh
├── requirements.txt
├── customer_data.xlsx
├── loan_data.xlsx
├── credit_system/
│   ├── settings.py
│   ├── urls.py
│   ├── celery.py
│   └── wsgi.py
└── credit_app/
    ├── models.py
    ├── views.py
    ├── serializers.py
    ├── urls.py
    ├── tasks.py
    └── utils.py
```

## How to Run

### Prerequisites
- Docker Desktop installed and running

### Steps

**1. Clone the repository**
```bash
git clone <your-repo-url>
cd credit_system
```

**2. Start all services**
```bash
docker compose up --build
```

This will automatically:
- Start PostgreSQL, Redis, Django and Celery
- Run all migrations
- Start the API server at `http://localhost:8000`

**3. Load the initial data**

Open a new terminal and run:
```bash
docker compose exec web python manage.py shell -c "from credit_app.tasks import ingest_all_data; ingest_all_data.delay()"
```

This loads all customer and loan data from the Excel files into the database via Celery in the background.

**4. Fix the ID sequence** (run once after data ingestion)
```bash
docker compose exec db psql -U postgres -d credit_db -c "SELECT setval('customers_customer_id_seq', (SELECT MAX(customer_id) FROM customers));"
docker compose exec db psql -U postgres -d credit_db -c "SELECT setval('loans_loan_id_seq', (SELECT MAX(loan_id) FROM loans));"
```

---

## API Endpoints

### 1. Register Customer
**POST** `/register`

Request:
```json
{
    "first_name": "John",
    "last_name": "Doe",
    "age": 30,
    "monthly_income": 50000,
    "phone_number": 9999999999
}
```

Response:
```json
{
    "customer_id": 301,
    "name": "John Doe",
    "age": 30,
    "monthly_income": 50000,
    "approved_limit": 1800000,
    "phone_number": 9999999999
}
```

---

### 2. Check Loan Eligibility
**POST** `/check-eligibility`

Request:
```json
{
    "customer_id": 1,
    "loan_amount": 100000,
    "interest_rate": 10,
    "tenure": 12
}
```

Response:
```json
{
    "customer_id": 1,
    "approval": true,
    "interest_rate": 10,
    "corrected_interest_rate": 12,
    "tenure": 12,
    "monthly_installment": 8978.71
}
```

---

### 3. Create Loan
**POST** `/create-loan`

Request:
```json
{
    "customer_id": 301,
    "loan_amount": 100000,
    "interest_rate": 14,
    "tenure": 12
}
```

Response:
```json
{
    "loan_id": 1001,
    "customer_id": 301,
    "loan_approved": true,
    "message": "Loan approved successfully",
    "monthly_installment": 8978.71
}
```

---

### 4. View Loan
**GET** `/view-loan/<loan_id>`

Response:
```json
{
    "loan_id": 1,
    "customer": {
        "id": 1,
        "first_name": "Aaron",
        "last_name": "Garcia",
        "phone_number": 9629317944,
        "age": 63
    },
    "loan_amount": 900000.0,
    "interest_rate": 17.92,
    "monthly_installment": 39978.0,
    "tenure": 120
}
```

---

### 5. View All Loans by Customer
**GET** `/view-loans/<customer_id>`

Response:
```json
[
    {
        "loan_id": 7798,
        "loan_amount": 900000.0,
        "interest_rate": 17.92,
        "monthly_installment": 39978.0,
        "repayments_left": 86
    }
]
```

---

## Credit Score Logic

Credit score is calculated out of 100 based on:

| Component | Description | Weight |
|-----------|-------------|--------|
| EMIs paid on time | Ratio of on-time payments | 35 pts |
| Number of past loans | Fewer loans = better score | 20 pts |
| Loan activity this year | Less recent borrowing = better | 20 pts |
| Loan volume vs limit | Lower utilization = better | 25 pts |

**Approval rules:**

| Credit Score | Decision |
|-------------|----------|
| > 50 | Approved at any interest rate |
| 30 – 50 | Approved only if rate ≥ 12% |
| 10 – 30 | Approved only if rate ≥ 16% |
| < 10 | Rejected |

Additional rule: if current EMIs exceed 50% of monthly salary, loan is rejected regardless of score.
