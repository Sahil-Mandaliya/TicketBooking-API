# 🎟️ Ticketing Platform

A robust backend system built with **Django** and **MySQL** designed to handle "thundering herd" scenarios where thousands of users compete for the last available ticket simultaneously.

---

## 🛠️ Tech Stack

-   **Language:** Python 3.11
-   **Framework:** Django 5.0 + Django REST Framework
-   **Database:** MySQL 8.0 (Selected for ACID compliance and Row-Level Locking)
-   **Containerization:** Docker & Docker Compose

---

## 🚀 Getting Started

### 1. Prerequisites

-   [Docker Desktop](https://www.docker.com/products/docker-desktop/)
-   `make` (standard on macOS/Linux)

### 2. Environment Setup

The project uses a `.env` file for secrets. Create one in the root directory:

```env
DEBUG=1
DB_HOST=db
DB_PORT=3306
DB_NAME=ticket_db
DB_USER=root
DB_PASSWORD=ticket_root_pass
MYSQL_ROOT_PASSWORD=ticket_root_pass
```

### 3. Installation & Run

1. Build and start the containers

```bash
make build
make up
```

2. In a NEW terminal, run migrations to setup the database

```bash
make migrations
make migrate
```

3. (Optional) Run the concurrency stress tests

```bash
make test
```

### 4. Project Structure

```plaintext
.
├── main/               # Project configuration (settings, urls)
├── ticketing/          # App logic
│   ├── migrations/     # Auto-generated DB schemas
│   ├── models.py       # Event & Booking schemas with indexing
│   ├── views.py        # Atomic booking logic & Locking
│   └── tests.py        # Concurrency thread tests
├── Makefile            # Orchestration shortcuts
├── docker-compose.yml  # Infrastructure
├── Dockerfile          # Python environment
└── requirements.txt    # Dependencies
```

### 5. API Endpoints

1. Initialize Event

```bash
POST /api/events/init/

Body: {"name": "Summer Fest", "tickets": 100}
```

2. Book Ticket

```bash
POST /api/tickets/book/

Body: {"event_id": 1, "user_id": "user_123", "number_of_tickets": 1}
```

Constraint: Max 2 tickets per user. Handles race conditions via select_for_update().

3. Cancel Ticket

```bash
POST /api/tickets/cancel/

Body: {"event_id": 1, "user_id": "user_123", "quantity": 1}
```

### 6. Concurrency Strategy

The system prevents overbooking by using Row level (event level) Locking and Atomic Transactions.

When a user attempts to book, the specific row for that Event is locked in MySQL. Any other simultaneous requests for the same event must wait until the first transaction commits. This ensures that the available_tickets count is always accurate.

### 7. Postman Collection

The Postman collection is available in the repository at:
`TicketBooking/Ticketing Platform API.postman_collection.json`
