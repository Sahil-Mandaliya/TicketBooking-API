import threading
from django.test import TransactionTestCase
from django.urls import reverse
from django.db import connections
from .models import Event, Booking
from rest_framework.test import APIClient
from rest_framework import status


class TicketingConcurrencyTest(TransactionTestCase):
    # Serialized rollback ensures the data created in setUp is
    # visible to all threads in a TransactionTestCase
    serialized_rollback = True

    def setUp(self):
        # Create an event with exactly 3 tickets
        self.event = Event.objects.create(name="Hot Concert", available_tickets=3)
        self.url = reverse("book-ticket")

    def attempt_booking(self, user_id, results):
        """
        Function executed by threads to simulate concurrent API calls.
        """
        client = APIClient()
        payload = {
            "event_id": self.event.id,
            "user_id": user_id,
            "number_of_tickets": 1,
        }
        try:
            # We use a try/except because if the DB deadlocks, the client
            # might throw an exception instead of a 400 status.
            response = client.post(self.url, payload, format="json")
            results.append(response.status_code)
        except Exception as e:
            results.append(500)
        finally:
            # Manually close connection for this thread
            connections.close_all()

    def test_race_condition_for_last_seats(self):
        """
        GIVEN 3 tickets are available
        WHEN 10 different users try to book at the exact same time
        THEN exactly 3 should succeed and 7 should fail.
        """
        threads = []
        results = []

        # We spawn 10 threads
        for i in range(10):
            t = threading.Thread(
                target=self.attempt_booking, args=(f"user_thread_{i}", results)
            )
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        successes = results.count(status.HTTP_200_OK)
        failures = results.count(status.HTTP_400_BAD_REQUEST)

        # Assertions
        self.assertEqual(
            successes, 3, f"Oversold! Successes: {successes}, Results: {results}"
        )
        self.assertEqual(failures, 7)

        # Final DB check
        self.event.refresh_from_db()
        self.assertEqual(self.event.available_tickets, 0)

    def test_single_user_concurrency_limit(self):
        """
        GIVEN 10 tickets are available
        WHEN 1 user tries to book 1 ticket 5 times simultaneously
        THEN exactly 2 should succeed (MAX_TICKETS_PER_USER) and 3 should fail.
        """
        self.event.available_tickets = 10
        self.event.save()

        threads = []
        results = []
        shared_user_id = "concurrent_user_99"

        for _ in range(5):
            t = threading.Thread(
                target=self.attempt_booking, args=(shared_user_id, results)
            )
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        successes = results.count(status.HTTP_200_OK)
        self.assertEqual(successes, 2, f"User bypassed limit! Successes: {successes}")

        # Verify the DB reflects exactly 2 tickets for this user
        booking = Booking.objects.get(event=self.event, user_id=shared_user_id)
        self.assertEqual(booking.quantity, 2)
