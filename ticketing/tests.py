import threading
from django.test import TransactionTestCase
from django.urls import reverse
from .models import Event, Booking
from rest_framework.test import APIClient


class ConcurrencyTest(TransactionTestCase):
    def setUp(self):
        self.event = Event.objects.create(name="Hot Concert", available_tickets=3)
        self.url = reverse("book-ticket")

    def attempt_booking(self, user_id, results):
        client = APIClient()
        response = client.post(
            self.url, {"event_id": self.event.id, "user_id": user_id}, format="json"
        )
        results.append(response.status_code)

    def test_race_condition(self):
        threads = []
        results = []

        # Simulate 10 users trying to book 3 available tickets
        for i in range(10):
            t = threading.Thread(
                target=self.attempt_booking, args=(f"user_{i}", results)
            )
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Check outcomes
        successes = results.count(200)
        failures = results.count(400)

        self.assertEqual(successes, 3)  # Only 3 should succeed
        self.assertEqual(failures, 7)  # 7 should get "Sold out"

        self.event.refresh_from_db()
        self.assertEqual(self.event.available_tickets, 0)
