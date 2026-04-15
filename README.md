# Library Management System

A full-stack web application for managing a library's books, members, and borrowing records. Built with **FastAPI** (backend) and **Next.js** (frontend).

---

## Tech Stack

| Layer     | Technology                                                    |
| --------- | ------------------------------------------------------------- |
| Backend   | Python 3.11+, FastAPI, SQLAlchemy 2.0, Pydantic v2, Alembic  |
| Frontend  | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS   |
| Database  | PostgreSQL 14+                                                |
| Auth      | JWT (access + refresh tokens), bcrypt password hashing        |
| Testing   | pytest (backend, 195 tests), Jest + React Testing Library (frontend, 228 tests) |

---

## Features

- **Books** — CRUD with ISBN validation, multi-author support, category tagging, copy tracking
- **Members** — CRUD with auto-generated library IDs (`LIBU0001`, …), email uniqueness
- **Borrowing** — Borrow / return flow with available-copy enforcement (DB trigger), overdue auto-detection
- **Authors & Categories** — Dedicated management with per-author borrowing statistics
- **Dashboard** — Summary stats, recent activity, most borrowed books
- **Authentication** — Login / logout with JWT access & refresh tokens, role-based access (admin / manager)
- **Search & Sort** — Server-driven sorting and full-text search across all list views
- **Rate Limiting** — Per-endpoint rate limits via SlowAPI
- **Structured Logging** — JSON logs with correlation IDs (`X-Request-ID`)

---

## Prerequisites

| Tool       | Version  | Notes                          |
| ---------- | -------- | ------------------------------ |
| Python     | ≥ 3.11   |                                |
| Node.js    | ≥ 18     |                                |
| PostgreSQL | ≥ 14     | Running and accessible locally |

---

## Getting Started

### 1. Clone the repository

```bash
git clone <repository-url>
cd numinolabs_assignment
```

### 2. Set up the database

Create a PostgreSQL database:

```bash
createdb numinolabs_assignment
```

### 3. Backend setup

```bash
cd backend

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
```

Edit `backend/.env` and set the required values:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/numinolabs_assignment
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
```

Run database migrations and seed data:

```bash
alembic upgrade head           # Apply all migrations
python -m seed                 # Seed 1000 books, 200 members, 2000+ borrowings
```

Start the API server:

```bash
uvicorn main:app --reload --port 8000
```

The API is now available at **http://localhost:8000**. Interactive docs at **http://localhost:8000/docs**.

### 4. Frontend setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment (default points to localhost:8000)
# Edit .env.local if your backend runs on a different host/port:
#   NEXT_PUBLIC_API_URL=http://localhost:8000

# Start the dev server
npm run dev
```

The app is now available at **http://localhost:3000**.

### 5. Login

Use the seeded credentials to log in:

| Role    | Email                | Password    |
| ------- | -------------------- | ----------- |
| Admin   | admin@library.com    | admin123    |
| Manager | manager@library.com  | manager123  |

> These credentials are for **development only**.

---

## Running Tests

### Backend (pytest)

```bash
cd backend
source .venv/bin/activate

# Run all tests
python -m pytest tests/ -q

# Run with verbose output
python -m pytest tests/ -v

# Run a specific test file
python -m pytest tests/test_books.py -v
```

**195 tests** across 8 test modules covering all API endpoints, CRUD operations, RBAC, and edge cases.

### Frontend (Jest + React Testing Library)

```bash
cd frontend

# Run all tests
npm test

# Run in watch mode
npm run test:watch

# Run with coverage report
npm run test:coverage
```

**228 tests** across 34 test suites covering pages, components, hooks, utilities, and API layer.

---

## Project Structure

```
numinolabs_assignment/
├── .gitignore
├── backend/
│   ├── alembic/                  # Database migration scripts
│   ├── alembic.ini               # Alembic configuration
│   ├── api/
│   │   ├── deps.py               # Shared dependencies (auth, pagination, DB session)
│   │   ├── exceptions.py         # Custom HTTP exceptions
│   │   └── v1/
│   │       ├── router.py         # Route registration
│   │       └── endpoints/        # Route handlers (auth, books, members, borrows, ...)
│   ├── config/
│   │   ├── database.py           # SQLAlchemy engine & session setup
│   │   └── settings.py           # Pydantic settings (env-driven)
│   ├── core/
│   │   ├── limiter.py            # Rate limiter instance
│   │   ├── logging.py            # Structured JSON logging
│   │   ├── redis_client.py       # Optional Redis connection
│   │   └── security.py           # JWT creation/verification, password hashing
│   ├── crud/                     # Data access layer
│   ├── models/                   # SQLAlchemy ORM models
│   ├── schemas/                  # Pydantic request/response schemas
│   ├── services/                 # Business logic layer (orchestrates CRUD + enforces rules)
│   │   ├── auth.py               # Login, logout, token refresh, user management
│   │   ├── author.py             # Author CRUD and borrowing statistics
│   │   ├── book.py               # Book creation/update, ISBN conflict, author/category validation
│   │   ├── borrow.py             # Borrow/return flow, availability enforcement, overdue detection
│   │   ├── category.py           # Category CRUD
│   │   ├── dashboard.py          # Aggregated summary statistics
│   │   └── member.py             # Member CRUD, email uniqueness, borrowing stats
│   ├── tests/                    # Pytest suites and fixtures
│   ├── main.py                   # FastAPI app factory & middleware
│   ├── pyproject.toml            # Python tooling configuration
│   ├── requirements.txt          # Runtime dependencies
│   ├── requirements-dev.txt      # Development dependencies
│   └── seed.py                   # Database seeding script
│
├── frontend/
│   ├── package.json              # Frontend scripts and dependencies
│   └── src/
│       ├── __tests__/            # Jest and React Testing Library suites
│       ├── app/                  # Next.js App Router pages and layouts
│       │   ├── authors/          # Author detail page
│       │   ├── books/            # Book list and detail pages
│       │   ├── borrowings/       # Borrowing list page
│       │   ├── dashboard/        # Dashboard with summary stats
│       │   ├── login/            # Login page
│       │   ├── members/          # Member list and detail pages
│       │   ├── layout.tsx        # Root app layout
│       │   ├── page.tsx          # App entry page
│       │   └── globals.css       # Global Tailwind styles
│       ├── components/
│       │   ├── books/            # Book-specific components
│       │   ├── borrowings/       # Borrowing-specific components
│       │   ├── layout/           # App shell, sidebar, auth guard
│       │   ├── members/          # Member-specific components
│       │   └── ui/               # Reusable UI primitives (Button, Dialog, Table, ...)
│       ├── hooks/                # Custom React hooks
│       ├── lib/
│       │   ├── api-endpoints.ts  # Centralized API path constants
│       │   ├── api.ts            # API client with token refresh
│       │   ├── constants.ts      # Shared UI and domain constants
│       │   ├── errors.ts         # Error normalization and toast helpers
│       │   ├── queries/          # TanStack React Query hooks
│       │   ├── routes.ts         # Centralized route constants
│       │   └── utils.ts          # Shared utilities
│       ├── providers/            # React context providers (auth, query client)
│       ├── types/                # Shared frontend TypeScript types
│       └── middleware.ts         # Next.js auth redirect middleware
│
└── README.md
```

---

## Backend Architecture

The backend follows a **three-tier layered architecture** to separate concerns and keep each layer focused:

```
HTTP Request
     │
     ▼
Endpoints  (api/v1/endpoints/)   — request parsing, auth, input validation, response shaping
     │
     ▼
Services   (services/)           — business logic, cross-entity rules, error translation
     │
     ▼
CRUD       (crud/)               — database queries via SQLAlchemy ORM (no business logic)
     │
     ▼
Database   (PostgreSQL)
```

### Service layer responsibilities

| Module | Responsibilities |
| --------------- | --------------------------------------------------------------------------- |
| `auth.py`       | Constant-time login (prevents user enumeration), token issuance, revocation, user CRUD |
| `book.py`       | ISBN conflict detection, author / category existence checks, copy tracking  |
| `borrow.py`     | Availability enforcement, duplicate-borrow prevention, overdue flag setting, race-condition handling |
| `member.py`     | Auto-generated library ID, email uniqueness across create/update, borrowing stats |
| `author.py`     | Author CRUD, per-author borrowing statistics aggregation                    |
| `category.py`   | Category CRUD with uniqueness enforcement                                   |
| `dashboard.py`  | Cross-entity aggregation for summary stats and activity feed                |

> **Endpoints never call CRUD directly.** All business operations go through the service layer so that validation, logging, and error translation are applied consistently.

---

## API Overview

All endpoints are prefixed with `/api/v1`. Protected routes require a `Bearer` token in the `Authorization` header.

| Method   | Endpoint                     | Description                     | Auth |
| -------- | ---------------------------- | ------------------------------- | ---- |
| `POST`   | `/auth/login`                | Obtain access + refresh tokens  | No   |
| `POST`   | `/auth/refresh`              | Refresh an access token         | No   |
| `POST`   | `/auth/logout`               | Revoke tokens                   | Yes  |
| `GET`    | `/auth/me`                   | Current user profile            | Yes  |
| `GET`    | `/health`                    | Service health check            | No   |
| `GET`    | `/books/`                    | List books (search, sort, filter) | Yes |
| `POST`   | `/books/`                    | Create a book                   | Yes  |
| `GET`    | `/books/{id}`                | Get book details                | Yes  |
| `PATCH`  | `/books/{id}`                | Update a book                   | Yes  |
| `DELETE` | `/books/{id}`                | Delete a book                   | Yes  |
| `GET`    | `/members/`                  | List members                    | Yes  |
| `POST`   | `/members/`                  | Create a member                 | Yes  |
| `GET`    | `/members/{id}`              | Get member details              | Yes  |
| `PATCH`  | `/members/{id}`              | Update a member                 | Yes  |
| `DELETE` | `/members/{id}`              | Delete a member                 | Yes  |
| `GET`    | `/borrows/`                  | List borrowing records          | Yes  |
| `POST`   | `/borrows/`                  | Borrow a book                   | Yes  |
| `PATCH`  | `/borrows/{id}/return`       | Return a borrowed book          | Yes  |
| `GET`    | `/authors/`                  | List authors                    | Yes  |
| `POST`   | `/authors/`                  | Create an author                | Yes  |
| `GET`    | `/categories/`               | List categories                 | Yes  |
| `POST`   | `/categories/`               | Create a category               | Yes  |
| `GET`    | `/dashboard/`                | Dashboard summary statistics    | Yes  |

Full interactive documentation is available at `/docs` (Swagger UI) when running in development mode.

---

## Environment Variables

### Backend (`backend/.env`)

| Variable                        | Required | Default                | Description                                |
| ------------------------------- | -------- | ---------------------- | ------------------------------------------ |
| `DATABASE_URL`                  | Yes      | —                      | PostgreSQL connection string               |
| `SECRET_KEY`                    | Yes      | —                      | JWT signing key (min 32 chars)             |
| `ENVIRONMENT`                   | No       | `development`          | `development` / `staging` / `production`   |
| `CORS_ORIGINS`                  | No       | `["http://localhost:3000"]` | Allowed CORS origins                  |
| `ACCESS_TOKEN_EXPIRE_MINUTES`   | No       | `30`                   | JWT access token lifetime                  |
| `REFRESH_TOKEN_EXPIRE_MINUTES`  | No       | `10080` (7 days)       | JWT refresh token lifetime                 |
| `REDIS_URL`                     | No       | `None`                 | Redis URL for token blocklist (recommended in production) |
| `LOG_LEVEL`                     | No       | `INFO`                 | Logging level                              |

### Frontend (`frontend/.env.local`)

| Variable              | Required | Default                  | Description        |
| --------------------- | -------- | ------------------------ | ------------------ |
| `NEXT_PUBLIC_API_URL`  | No       | `http://localhost:8000`  | Backend API URL    |
