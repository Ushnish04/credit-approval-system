# Credit Approval System

A backend system for managing credit approvals built with Django, Celery, PostgreSQL and Redis — fully dockerized.

## Tech Stack

- **Django 5.2** + Django REST Framework
- **PostgreSQL** — database
- **Celery** + **Redis** — background task queue for data ingestion
- **Docker** + **Docker Compose** — containerization

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running

That's it. No Python, no PostgreSQL, no Redis needed on your machine.

## Quick Start

**1. Clone the repository**
```bash
git clone <https://github.com/Ushnish04/credit-approval-system/tree/main>
cd credit_system
```

**2. Start all services**
```bash
docker compose up --build
```

This automatically:
- Starts PostgreSQL, Redis, Django and Celery
- Runs all migrations
- Starts the API at `http://localhost:8000`

**3. Load initial data**

Open a new terminal:
```bash
docker compose exec web python manage.py shell -c "from credit_app.tasks import ingest_all_data; ingest_all_data.delay()"
```

This loads all customer and loan data from the Excel files into the database in the background. Wait a few seconds for it to complete.

**4. Start using the API at `http://localhost:8000`**

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

Score calculated out of 100:

| Component | Weight |
|-----------|--------|
| EMIs paid on time | 35 pts |
| Number of past loans | 20 pts |
| Loan activity this year | 20 pts |
| Loan volume vs approved limit | 25 pts |

**Approval rules:**

| Credit Score | Decision |
|-------------|----------|
| > 50 | Approved at any interest rate |
| 30 – 50 | Approved only if rate ≥ 12% |
| 10 – 30 | Approved only if rate ≥ 16% |
| < 10 | Rejected |

Extra rule: if current EMIs > 50% of monthly salary → rejected regardless of score.
