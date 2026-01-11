from django.db import transaction
from django.db.models import F
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ticketing.models import Event, Booking
from ticketing.constants import MAX_TICKETS_PER_USER, BookingStatus


class InitializeEventView(APIView):
    """
    Endpoint: /api/events/init/
    Purpose: Create an event with a pool of tickets.
    """

    def post(self, request):
        name = request.data.get("name")
        tickets = request.data.get("tickets")

        if not name or tickets is None:
            return Response(
                {"error": "Missing name or tickets"}, status=status.HTTP_400_BAD_REQUEST
            )

        event = Event.objects.create(name=name, available_tickets=tickets)
        return Response(
            {"id": event.id, "name": name, "available_tickets": tickets},
            status=status.HTTP_201_CREATED,
        )


class BookTicketView(APIView):
    def post(self, request):
        event_id = request.data.get("event_id")
        user_id = request.data.get("user_id")
        # Ensure quantity is an integer
        try:
            quantity = int(request.data.get("number_of_tickets", 0))
        except (ValueError, TypeError):
            return Response({"error": "Invalid quantity"}, status=400)

        if not event_id or not user_id or quantity <= 0:
            return Response({"error": "Invalid input data"}, status=400)

        try:
            with transaction.atomic():
                # 1. Lock Event (Inventory Control)
                event = Event.objects.select_for_update().get(id=event_id)

                # 2. Lock User Booking (User Limit Control)
                # We use select_for_update() here so that two rapid requests from
                # the SAME user wait for each other.
                booking, created = Booking.objects.select_for_update().get_or_create(
                    event=event,
                    user_id=user_id,
                    defaults={"quantity": 0, "status": BookingStatus.PENDING},
                )

                # 3. Handle 'Cancelled' status re-entry
                # If the user previously cancelled everything, reset status to PENDING/CONFIRMED
                if booking.status == BookingStatus.CANCELLED:
                    booking.quantity = 0

                # 4. Check Limit (Logic: Current + New <= Max)
                if booking.quantity + quantity > MAX_TICKETS_PER_USER:
                    return Response(
                        {
                            "error": f"Limit exceeded. You already have {booking.quantity} tickets."
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # 5. Check Inventory
                if event.available_tickets < quantity:
                    return Response({"error": "Sold out"}, status=400)

                # 6. Atomic Updates
                event.available_tickets = F("available_tickets") - quantity
                event.save()

                booking.quantity = F("quantity") + quantity
                booking.status = BookingStatus.CONFIRMED
                booking.save()

            return Response({"message": "Booking successful"}, status=200)

        except Event.DoesNotExist:
            return Response({"error": "Event not found"}, status=404)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CancelTicketView(APIView):
    def post(self, request):
        event_id = request.data.get("event_id")
        user_id = request.data.get("user_id")
        cancel_qty = int(request.data.get("quantity", 1))

        try:
            with transaction.atomic():
                # Lock both to prevent race conditions during return
                booking = Booking.objects.select_for_update().get(
                    event_id=event_id, user_id=user_id
                )
                event = Event.objects.select_for_update().get(id=event_id)

                if booking.quantity < cancel_qty:
                    return Response(
                        {"error": "Cannot cancel more than booked"}, status=400
                    )

                # Return tickets to pool
                event.available_tickets = F("available_tickets") + cancel_qty
                event.save()

                # Update status if they have zero tickets left
                new_qty = (
                    booking.quantity - cancel_qty
                )  # Local calculation for status check

                # Note: Since we used F(), we should refresh or use logic:
                if new_qty == 0:
                    booking.status = BookingStatus.CANCELLED

                booking.quantity = new_qty
                booking.save()

            return Response({"message": "Cancellation successful"})
        except Booking.DoesNotExist:
            return Response({"error": "No booking found"}, status=404)
