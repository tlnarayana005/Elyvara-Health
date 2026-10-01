# EVE Healthcare — Diagnostic Test Booking Platform

Backend service for managing diagnostic centres, tests, bookings, and payments.  
Built as part of the **EVE Healthcare SDE Intern Backend Engineering Assignment**.

---

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Tech Stack](#tech-stack)
3. [Architecture](#architecture)
4. [Folder Structure](#folder-structure)
5. [Database Design](#database-design)
6. [Setup Instructions](#setup-instructions)
7. [API Endpoints](#api-endpoints)
8. [Authentication Flow](#authentication-flow)
9. [Authorization Model](#authorization-model)
10. [Booking State Machine](#booking-state-machine)
11. [Payment Flow](#payment-flow)
12. [Webhook Idempotency](#webhook-idempotency)
13. [Edge Cases Handled](#edge-cases-handled)
14. [Running Tests](#running-tests)
15. [Seed Data](#seed-data)
16. [Example Requests](#example-requests)
17. [Assumptions](#assumptions)
18. [What I Would Improve](#what-i-would-improve)

---

## Problem Statement

Build a backend system where:

- Users can **sign up and log in** (JWT-based authentication)
- Admins can **manage diagnostic centres and tests**
- Authenticated users can **browse** centres/tests, **book** diagnostic tests, and **pay** for bookings
- A **simulated payment provider** sends webhook callbacks to confirm or fail payments
- Webhooks must be **idempotent** — processing the same event multiple times must not create duplicates or corrupt state

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| Framework | Flask 3.0 |
| ORM | SQLAlchemy 2.x / Flask-SQLAlchemy |
| Database | PostgreSQL |
| Migrations | Alembic |
| Auth | bcrypt + PyJWT |
| Testing | pytest |
| Config | python-dotenv |

---

## Architecture

The application uses the **Flask Application Factory** pattern with **Blueprints** for modular route registration.

```
Request → Flask Route → Service Function → SQLAlchemy Model → PostgreSQL
```

- **Routes** (`app/routes/`) — HTTP handling, request parsing, response formatting
- **Services** (`app/services/`) — Business logic, state machine validation, transactions
- **Models** (`app/models/`) — Database schema, relationships, serialization
- **Utils** (`app/utils/`) — Cross-cutting: JWT auth, password hashing, error handling

---

## Folder Structure

```
eve_health_care/
├── app/
│   ├── __init__.py          # App factory
│   ├── config.py            # Environment-based configuration
│   ├── extensions.py        # SQLAlchemy instance
│   ├── seed.py              # Database seed script
│   ├── models/
│   │   ├── __init__.py      # Model imports
│   │   ├── user.py
│   │   ├── diagnostic_centre.py
│   │   ├── diagnostic_test.py  # DiagnosticTest + CentreTest
│   │   ├── booking.py
│   │   ├── payment.py
│   │   └── webhook_event.py
│   ├── routes/
│   │   ├── auth.py
│   │   ├── centres.py
│   │   ├── tests.py
│   │   ├── bookings.py
│   │   └── payments.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── booking_service.py
│   │   ├── payment_service.py
│   │   └── webhook_service.py
│   └── utils/
│       ├── auth.py          # bcrypt, JWT, decorators
│       └── errors.py        # APIError + global handlers
├── tests/
│   ├── conftest.py          # Fixtures
│   ├── test_auth.py
│   ├── test_centres.py
│   ├── test_bookings.py
│   ├── test_payments.py
│   └── test_webhooks.py
├── migrations/              # Alembic migrations
├── .env.example
├── .gitignore
├── requirements.txt
├── run.py
└── README.md
```

---

## Database Design

### Entity-Relationship Diagram

```
Users 1──* Bookings *──1 CentreTests
                              │
              ┌───────────────┼───────────────┐
              │                               │
    DiagnosticCentres                  DiagnosticTests

Bookings 1──* Payments

WebhookEvents (standalone — stores processed events for idempotency)
```

### Tables

| Table | Key Columns | Purpose |
|-------|------------|---------|
| `users` | id, name, email (UNIQUE), password_hash, is_admin | User accounts |
| `diagnostic_centres` | id, name, location | Physical lab locations |
| `diagnostic_tests` | id, name, description | Types of tests available |
| `centre_tests` | id, centre_id (FK), test_id (FK), price | Many-to-many with price — a test can cost differently at different centres |
| `bookings` | id, user_id (FK), centre_test_id (FK), appointment_datetime, amount, status | User bookings |
| `payments` | id, booking_id (FK), provider_payment_id (UNIQUE), amount, status | Payment records |
| `webhook_events` | id, event_id (UNIQUE), event_type, payload, processed_at | Idempotency tracking |

### Why `centre_tests`?

A centre can offer many tests. A test can be offered by many centres. The **price varies by centre**. This is a classic many-to-many relationship with an extra attribute (price), so an association table is the correct relational design.

### Key Constraints

- `users.email` — UNIQUE
- `centre_tests(centre_id, test_id)` — UNIQUE (prevents duplicate centre-test pairs)
- `payments.provider_payment_id` — UNIQUE
- `webhook_events.event_id` — UNIQUE (idempotency key)
- All foreign keys use `ON DELETE CASCADE`
- All timestamps use UTC

---

## Setup Instructions

### Prerequisites

- Python 3.11+
- PostgreSQL running locally (port 5432)

### 1. Clone and install

```bash
git clone <your-repo-url>
cd eve_health_care
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Create databases

```bash
python create_dbs.py
```

Or manually in psql:
```sql
CREATE DATABASE eve_healthcare;
CREATE DATABASE eve_healthcare_test;
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env with your PostgreSQL credentials
```

### 4. Run migrations

```bash
python -m alembic upgrade head
```

### 5. Seed sample data

```bash
python -m app.seed
```

### 6. Start the server

```bash
python run.py
```

Server starts at `http://localhost:5001`

---

## API Endpoints

| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| `GET` | `/health` | No | Health check |
| **Auth** | | | |
| `POST` | `/auth/signup` | No | Register a new user |
| `POST` | `/auth/login` | No | Login, receive JWT |
| **Centres** | | | |
| `GET` | `/centres/` | JWT | List all centres |
| `GET` | `/centres/<id>` | JWT | Get centre details |
| `POST` | `/centres/` | Admin | Create a centre |
| `PATCH` | `/centres/<id>` | Admin | Update a centre |
| `GET` | `/centres/<id>/tests` | JWT | List tests at a centre (with prices) |
| **Tests** | | | |
| `GET` | `/tests/` | JWT | List all diagnostic tests |
| `GET` | `/tests/<id>` | JWT | Get test details |
| `POST` | `/tests/` | Admin | Create a test |
| `PATCH` | `/tests/<id>` | Admin | Update a test |
| `POST` | `/tests/centre-tests` | Admin | Link a test to a centre with a price |
| **Bookings** | | | |
| `POST` | `/bookings/` | JWT | Create a booking (price from DB) |
| `GET` | `/bookings/` | JWT | List own bookings |
| `GET` | `/bookings/<id>` | JWT | Get own booking |
| `POST` | `/bookings/<id>/cancel` | JWT | Cancel own booking |
| **Payments** | | | |
| `POST` | `/payments/` | JWT | Simulate payment for a booking |
| `POST` | `/payments/webhook/` | No* | Receive payment webhook |

*Webhooks come from external systems and don't use user JWT.

---

## Authentication Flow

### Signup

```
POST /auth/signup
{ "name": "Alice", "email": "alice@example.com", "password": "alice123" }

→ Validate input
→ Check email uniqueness
→ Hash password with bcrypt
→ Store user
→ Return user (without password_hash)
```

### Login

```
POST /auth/login
{ "email": "alice@example.com", "password": "alice123" }

→ Find user by email
→ Verify password with bcrypt
→ Generate JWT (contains user_id, exp, iat)
→ Return { token, user }
```

### Accessing Protected Routes

```
Authorization: Bearer <JWT>

→ Extract token from header
→ Decode and validate JWT (signature, expiry)
→ Load user from database
→ Set g.current_user
```

---

## Authorization Model

| Role | Can Do |
|------|--------|
| **USER** | Browse centres/tests, create/view/cancel own bookings, pay for own bookings |
| **ADMIN** | Everything USER can do + create/update centres, tests, and centre-test relationships |

- `@login_required` — enforces JWT authentication
- `@admin_required` — enforces `is_admin=True` (stacked after `@login_required`)
- Booking ownership — each service function checks `booking.user_id == current_user.id`

---

## Booking State Machine

```
                ┌─────────────┐
                │   PENDING   │
                └──────┬──────┘
                       │
          ┌────────────┼────────────┐
          │            │            │
          ▼            ▼            ▼
    ┌──────────┐ ┌──────────┐ ┌───────────┐
    │CONFIRMED │ │  FAILED  │ │ CANCELLED │
    └────┬─────┘ └────┬─────┘ └───────────┘
         │            │          (terminal)
         └────────────┘
                │
                ▼
          ┌───────────┐
          │ CANCELLED │
          └───────────┘
```

**Valid transitions:**

| From | To |
|------|----|
| PENDING | CONFIRMED, FAILED, CANCELLED |
| CONFIRMED | CANCELLED |
| FAILED | CANCELLED |
| CANCELLED | *(none — terminal)* |

**Key rules:**
- Clients cannot directly set status to CONFIRMED — that requires a successful payment
- Transition validation is centralized in `Booking.can_transition_to()`
- Payment success → CONFIRMED; Payment failure → FAILED; User action → CANCELLED

---

## Payment Flow

```
User calls POST /payments/ { booking_id: 5 }
    │
    ├─ Authenticate user (JWT)
    ├─ Verify booking exists
    ├─ Verify booking belongs to user
    ├─ Verify booking is PENDING (payable)
    ├─ Check no existing successful payment
    │
    ├─ Simulate payment result (SUCCESS or FAILED)
    ├─ Create Payment record
    ├─ Update Booking status
    ├─ Commit transaction (atomic)
    │
    └─ Return payment result
```

Both payment creation and booking status update happen in the **same database transaction**. If either fails, both are rolled back — this prevents inconsistent states like `payment=SUCCESS, booking=PENDING`.

The `simulate_failure` flag allows tests to deterministically produce failed payments.

---

## Webhook Idempotency

This is the most critical design element.

### The Problem

Payment providers may send the same webhook event multiple times (network retries, at-least-once delivery). Without idempotency, we could:
- Create duplicate payment records
- Transition a booking status multiple times
- Corrupt the database state

### The Solution

**Database-level idempotency using PostgreSQL UNIQUE constraints.**

```
webhook_events table:
  event_id  VARCHAR(255) UNIQUE NOT NULL
```

### Processing Flow

```
Incoming webhook { event_id: "evt_123", payment_id: "pay_abc", status: "SUCCESS" }
    │
    ├─ Validate payload
    │
    ├─ INSERT INTO webhook_events (event_id, ...)
    │   │
    │   ├─ SUCCESS: First time seeing this event → continue processing
    │   │   ├─ Find payment by provider_payment_id
    │   │   ├─ Update payment status
    │   │   ├─ Update booking status
    │   │   ├─ Mark event as processed
    │   │   └─ COMMIT
    │   │
    │   └─ IntegrityError: Duplicate event_id → ROLLBACK
    │       └─ Return "Event already processed" (200 OK)
    │
    └─ Done
```

### What happens when the same event arrives 3 times?

1. **Event #1**: INSERT succeeds → payment and booking updated → committed
2. **Event #2**: INSERT fails (UNIQUE violation) → rollback → return "already processed"
3. **Event #3**: Same as #2 — no side effects

**Result:** Exactly one logical processing, regardless of delivery count.

### Concurrency Safety

If two identical webhooks arrive at **nearly the same time**:
- Both try to INSERT the same event_id
- PostgreSQL's UNIQUE constraint ensures only one INSERT succeeds
- The losing transaction gets an `IntegrityError`, rolls back, and returns safely
- No race condition possible because the constraint is enforced at the database level

---

## Edge Cases Handled

### Authentication
- Duplicate email signup → 409
- Wrong password → 401
- Missing/invalid/expired JWT → 401
- Malformed Authorization header → 401

### Authorization
- Normal user tries to create/update centre/test → 403
- User tries to access another user's booking → 403
- User tries to cancel another user's booking → 403
- User tries to pay for another user's booking → 403

### Bookings
- Invalid centre_test_id → 404
- Past appointment datetime → 400
- Client-supplied amount is **ignored** — price always from database
- Invalid state transition (e.g., cancel an already-cancelled booking) → 409
- Nonexistent booking → 404

### Payments
- Payment for nonexistent booking → 404
- Payment for non-PENDING booking → 409
- Duplicate successful payment for same booking → 409
- Payment for another user's booking → 403

### Webhooks
- Duplicate event_id → safe return, no re-processing
- Unknown payment_id → 404
- Invalid status value → 400
- Malformed/missing payload fields → 400
- Empty request body → 400

---

## Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_webhooks.py -v

# Run a single test
python -m pytest tests/test_webhooks.py::TestWebhookIdempotency::test_duplicate_webhook_is_idempotent -v
```

Tests use a **separate test database** (`eve_healthcare_test`). Each test function gets a clean database (tables created before, dropped after).

### Test Coverage: 51 tests

- **Auth**: 11 tests (signup, login, JWT validation)
- **Centres/Tests**: 14 tests (CRUD, admin authorization, centre-test linking)
- **Bookings**: 12 tests (creation, server-side pricing, ownership, cancellation, state machine)
- **Payments**: 6 tests (success, failure, ownership, duplicates)
- **Webhooks**: 8 tests (success, failure, idempotency, edge cases)

---

## Seed Data

```bash
python -m app.seed
```

Creates:
- 1 admin user (`admin@eve.com` / `admin123`)
- 2 normal users (`alice@example.com` / `alice123`, `bob@example.com` / `bob12345`)
- 3 diagnostic centres (Mumbai, Delhi, Bangalore)
- 5 diagnostic tests (CBC, Lipid Profile, Thyroid, Liver Function, X-Ray)
- 11 centre-test relationships with varying prices

The seed is idempotent — running it again skips already-existing records.

---

## Example Requests

### Signup
```bash
curl -X POST http://localhost:5001/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "email": "alice@test.com", "password": "alice123"}'
```

### Login
```bash
curl -X POST http://localhost:5001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com", "password": "alice123"}'
```

### Create Booking
```bash
curl -X POST http://localhost:5001/bookings/ \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"centre_test_id": 1, "appointment_datetime": "2026-11-01T10:00:00"}'
```

### Make Payment
```bash
curl -X POST http://localhost:5001/payments/ \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"booking_id": 1}'
```

### Send Webhook
```bash
curl -X POST http://localhost:5001/payments/webhook/ \
  -H "Content-Type: application/json" \
  -d '{"event_id": "evt_123", "event_type": "payment.updated", "payment_id": "pay_abc123", "status": "SUCCESS"}'
```

---

## Assumptions

1. **No real payment gateway** — payments are simulated deterministically for testability
2. **Single-server deployment** — webhook concurrency is handled via PostgreSQL constraints, not distributed locks
3. **Webhooks are unauthenticated** — in production, you'd verify a signature/secret from the payment provider
4. **Admin is a boolean flag** — no complex RBAC; simple and sufficient for this scope
5. **No pagination** — omitted to keep scope focused; would add for production
6. **Appointment time is not slot-based** — no capacity/conflict checking for appointment slots

---

## What I Would Improve

Given more time and a production context:

- **Webhook signature verification** — authenticate incoming webhooks with HMAC signatures
- **Pagination** — for centres, tests, and bookings lists
- **Rate limiting** — protect auth endpoints from brute force
- **Structured logging** — JSON logs with request IDs for observability
- **Docker + docker-compose** — containerized PostgreSQL for easier local setup
- **Redis caching** — cache catalogue data (centres/tests) for faster reads
- **Celery** — async background processing for payment retries
- **Slot-based scheduling** — prevent double-booking of appointment times
- **Soft deletes** — instead of CASCADE deletes for audit trails
- **API versioning** — `/api/v1/` prefix for future backward compatibility
- **OpenAPI/Swagger** — auto-generated API documentation
