# EVE Healthcare — Diagnostic Test Booking Platform

Full-stack app where users can browse diagnostic centres, book tests, and pay for appointments.  
Built for the **EVE Healthcare SDE Intern Assignment**.

**Backend:** Flask · SQLAlchemy · PostgreSQL · JWT · bcrypt · pytest  
**Frontend:** React · Vite · Redux Toolkit · Axios · Bootstrap

---

## Setup

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env                  # set your Postgres credentials
psql -U postgres -c "CREATE DATABASE eve_healthcare;"
psql -U postgres -c "CREATE DATABASE eve_healthcare_test;"
python -m alembic upgrade head
python -m app.seed                    # loads sample data
python run.py                         # → http://localhost:5001
```

### Frontend
```bash
cd frontend
npm install
npm run dev                           # → http://localhost:5173
```

### Seed Logins
| Role | Email | Password |
|------|-------|----------|
| Admin | admin@eve.com | admin123 |
| User | alice@example.com | alice123 |
| User | bob@example.com | bob12345 |

---

## Project Structure

```
backend/app/
  models.py      — User, Centre, Test, CentreTest, Booking, Payment, WebhookEvent
  routes.py      — all API endpoints
  services.py    — business logic (auth, booking, payment, webhook)
  auth.py        — JWT helpers, bcrypt, @login_required, @admin_required
  errors.py      — APIError class + global handlers
  seed.py        — sample data loader

frontend/src/
  pages/         — Home, Login, Signup, Centres, CentreDetails, Booking, MyBookings, BookingDetails, Admin
  components/    — Navbar, ProtectedRoute, StatusBadge
  services/      — Axios API calls
  store/         — Redux auth slice
```

---

## Database Design

| Table | Key Columns | Purpose |
|-------|-------------|---------|
| `users` | email (unique), password_hash, is_admin | Accounts |
| `diagnostic_centres` | name, location | Lab locations |
| `diagnostic_tests` | name, description | Test types |
| `centre_tests` | centre_id, test_id, **price** | Same test can cost differently at different centres |
| `bookings` | user_id, centre_test_id, amount, **status** | Appointments with state tracking |
| `payments` | booking_id, provider_payment_id (unique), status | Payment records |
| `webhook_events` | **event_id (unique)** | Idempotency — prevents duplicate webhook processing |

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/signup` | — | Register |
| POST | `/auth/login` | — | Login → JWT |
| GET | `/centres/` | JWT | List centres |
| GET | `/centres/:id` | JWT | Centre details |
| GET | `/centres/:id/tests` | JWT | Tests at centre with prices |
| POST | `/centres/` | Admin | Create centre |
| PATCH | `/centres/:id` | Admin | Update centre |
| GET | `/tests/` | JWT | List all tests |
| POST | `/tests/` | Admin | Create test |
| POST | `/tests/centre-tests` | Admin | Link test to centre with price |
| POST | `/bookings/` | JWT | Book a test |
| GET | `/bookings/` | JWT | My bookings |
| GET | `/bookings/:id` | JWT | Booking details (own only) |
| POST | `/bookings/:id/cancel` | JWT | Cancel booking |
| POST | `/payments/` | JWT | Pay for booking |
| POST | `/payments/webhook/` | — | Payment provider webhook |

---

## How It Works

### Authentication
- Passwords hashed with bcrypt, login returns a JWT
- `@login_required` validates JWT and sets `g.current_user`
- `@admin_required` checks `is_admin` flag (stacked after login_required)
- Booking ownership enforced in service layer — users can only access their own bookings

### Booking Flow
1. User browses centres → picks a test → selects date/time
2. Price is always taken from the DB (`centre_tests.price`), never from the client
3. Booking starts as PENDING

### Booking Status Transitions
```
PENDING → CONFIRMED  (payment success)
PENDING → FAILED     (payment failure)
PENDING → CANCELLED  (user cancels)
CONFIRMED → CANCELLED
FAILED → CANCELLED
CANCELLED → (terminal)
```
All transitions validated by `Booking.can_transition_to()` before any status change.

### Frontend
React SPA with Redux Toolkit for auth state (token + user in localStorage). Axios interceptor attaches the JWT to every request and redirects to login on 401. Pages use local state for forms/loading — Redux is only used for global auth. UI is Bootstrap with minimal custom CSS.

### Payment
Payment record + booking status update happen in a single DB transaction. If either fails, both roll back — prevents inconsistent states like `payment=SUCCESS, booking=PENDING`.

### Webhook Idempotency
Payment providers can send the same event multiple times. I handle this at the DB level:

1. Each webhook has a unique `event_id`
2. `webhook_events` table has a UNIQUE constraint on `event_id`
3. On INSERT: if it succeeds → first time, process it. If IntegrityError → duplicate, return "already processed"
4. Safe under concurrent requests — PostgreSQL enforces the constraint at the DB level, so only one of two simultaneous identical webhooks can win the INSERT

---

## Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

Uses separate `eve_healthcare_test` database. Tables are recreated for each test.

**Coverage:** signup/login/JWT validation, centres/tests CRUD + admin auth, booking creation + server-side pricing + ownership + state machine, payment success/failure/duplicates, webhook idempotency + concurrent duplicates.

---

## Assumptions

- Payments are simulated (no real gateway) — `simulate_failure` flag for testing
- Webhooks are unauthenticated (production would verify HMAC signatures)
- No pagination on list endpoints
- No appointment slot conflict checking
- Admin is a boolean flag, no complex role system
