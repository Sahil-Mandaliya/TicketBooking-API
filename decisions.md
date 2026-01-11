# Decisions

This document explains the key technical decisions made while building the ticket booking backend.

---

## 1. Database Choice and Structure

I used **MySQL with a relational schema** because ticket booking needs **strong consistency** and **safe concurrent updates**.

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

### Why this works well

**Strong consistency**  
Overbooking is not acceptable. If only **1 ticket** is available, only **one user** should be able to book it. MySQL transactions ensure this.

**Transactional safety**  
Ticket availability is updated inside a single transaction, so partial updates never occur.

**Row-level locking**  
During booking, the event row is locked using `SELECT ... FOR UPDATE`.  
This allows:

-   Safe handling when multiple users try to book the last ticket
-   Parallel bookings for different events

---

## 2. Handling Race Conditions

### Row-level locking (Chosen)

The event row is locked during the booking transaction.

**Example**

-   Event A has 1 ticket
-   User A locks the row and books successfully
-   User B waits, then sees 0 tickets and receives an error

**Why chosen**

-   Simple and reliable
-   Works well for high-contention cases
-   Prevents overbooking at the database level

---

### Optimistic locking / Retry-based approach (Rejected)

This approach retries the transaction if data changes.

**Why rejected**

-   For popular events, most requests would fail and retry
-   Causes unnecessary CPU load
-   Poor performance under heavy contention

---

### Application-level locks / Redis mutex (Rejected)

This approach uses Redis to manage locks.

**Why rejected**

-   Adds extra infrastructure complexity
-   Risk of stale locks if the application crashes
-   Database transactions already provide atomicity

---

## 3. Scaling to High Traffic (1M RPS)

### Current bottleneck

**Database row contention**

When many users try to book the same event:

-   All requests compete for the same database row
-   This limits scalability

---

### Scalable approach

**Step 1: Redis-based ticket counter**

-   Store available tickets in Redis
-   Use Lua scripts for atomic decrement

**Step 2: Asynchronous database writes**

-   After Redis confirms the booking:
    -   Send an event to Kafka / RabbitMQ
-   Background workers persist data to MySQL

This reduces database load and allows horizontal scaling.

---

## Summary

-   MySQL ensures correctness and consistency
-   Row-level locking prevents overbooking
-   Redis and async processing enable large-scale traffic

The design is simple, safe, and easy to scale.
