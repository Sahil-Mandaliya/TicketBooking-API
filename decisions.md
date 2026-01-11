. Why this database structure?
I chose a relational structure (MySQL) because it provides ACID compliance. In ticketing, consistency is more important than eventual consistency.

Event table: Stores the source of truth for inventory.

Booking table: Tracks user behavior.

Composite Index: The unique_together on (event, user_id) ensures we can quickly verify the "2 tickets per user" rule without scanning millions of rows.

2. Handling Race Conditions
   I used Pessimistic Locking + Atomic Updates.

Why not simple Python checks? If two requests read available_tickets = 1 at the same time, both will think they can book, resulting in -1 tickets (Overbooking).

The fix: Event.objects.filter(available_tickets\_\_gt=0).update(...). MySQL handles this update as an atomic operation. Only the requests that successfully "grab" the row lock and meet the > 0 criteria will succeed.

3. Bottleneck at 1 Million RPS
   At 1M RPS, the bottleneck becomes Database Row Contention.

Every request for "Event A" is trying to lock the same single row in MySQL.

MySQL can only process a few thousand updates per second on a single row before the "lock wait queue" explodes.

To fix this: We would move the "counter" to Redis using a Lua script to decrement the count in-memory, then lazily sync the results to MySQL.
