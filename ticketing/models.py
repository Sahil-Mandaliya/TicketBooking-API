from django.db import models
from ticketing.constants import BookingStatus


class Event(models.Model):
    name = models.CharField(max_length=255, unique=True)
    available_tickets = models.PositiveIntegerField()

    class Meta:
        indexes = [
            # Speeds up select_for_update() lookups by ID
            # (Though Primary Key handles this, explicit listing helps in complex queries)
            models.Index(
                fields=["id", "available_tickets"], name="idx_event_inventory"
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.available_tickets} left)"


class Booking(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="bookings")
    user_id = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, default=BookingStatus.PENDING)

    class Meta:
        # 1. Composite Unique Constraint (Acts as a unique index)
        # Crucial for preventing duplicate booking records per user.
        unique_together = ("event", "user_id")

        indexes = [
            # 2. Performance: Look up all bookings for a specific user across different events
            models.Index(fields=["user_id"], name="idx_booking_user_id"),
            # 3. Optimization: Filtering by status (e.g., getting all 'CONFIRMED' tickets)
            models.Index(fields=["status"], name="idx_booking_status"),
            # 4. Composite: For highly specific filtered queries (e.g., user's pending tickets)
            models.Index(fields=["user_id", "status"], name="idx_user_status_lookup"),
        ]
