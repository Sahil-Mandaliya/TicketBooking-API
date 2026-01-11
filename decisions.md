# Decisions

This document explains the key technical decisions made while building the ticket booking backend.

---

## 1. Why I chose this database structure

I chose **MySQL with a relational schema** because ticket booking requires **strong consistency** and **transaction safety**.

### Database structure (simplified)

-   **events**

    -   `id`
    -   `available_tickets`

-   **bookings**
    -   `id`
    -   `event_id`
    -   `user_id`
    -   `quantity`
    -   `status`

### Reasons for this choice

**ACID compliance**  
Ticket booking cannot allow overbooking. If only **1 ticket** is left, only **one user** should be able to book it. MySQL transactions guarantee this consistency.

**Row-level locking**  
During booking, I use `SELECT ... FOR UPDATE` to lock only the specific event row.  
This allows:

-   High concurrency across different events
-   Safe handling when multiple users try to book the last ticket

---

## 2. Race condition approaches considered

### Row-level locking (Chosen)

I lock the event row during the booking transaction.

**Example**  
If Event A has 1 ticket:

-   User A locks the row and books successfully
-   User B waits, then sees 0 tickets and gets an error

**Why chosen**

-   Very reliable for high-contention scenarios
-   Simple and safe at database level

---

### Optimistic locking (Redis level locking) (Rejected)

This approach uses a version field and retries if data changes.

**Why rejected**

-   For popular events, many requests would fail and retry
-   Causes high CPU usage and poor performance
-   Not suitable when many users fight for the same resource

---

### Application-level locks / Redis mutex

This approach uses Redis to lock the booking process.

**Why rejected**

-   Adds extra complexity
-   Risk of stale locks if the app crashes
-   Database transactions are simpler and fully atomic

---

## 3. Scaling to 1 Million Requests Per Second (RPS)

### Current bottleneck

**Database row contention**

When millions of users try to book the same event:

-   All requests compete for the same database row
-   MySQL cannot handle that level of contention efficiently

---

### Scalable approach

**Step 1: Use Redis for ticket count**

-   Store available tickets in Redis
-   Use Lua scripts to decrement tickets atomically

**Step 2: Async persistence**

-   Once Redis confirms booking:
    -   Push message to Kafka / RabbitMQ
-   Background workers write bookings to MySQL

This approach:

-   Handles massive traffic
-   Keeps MySQL consistent
-   Scales horizontally

---

## Summary

-   MySQL ensures correctness and consistency
-   Pessimistic locking safely handles race conditions
-   Redis + async writes enable large-scale traffic

This design is simple, reliable, and has a clear path to scale.
