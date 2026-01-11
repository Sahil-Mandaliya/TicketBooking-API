from django.urls import path
from ticketing.views import InitializeEventView, BookTicketView, CancelTicketView

urlpatterns = [
    path("events/init/", InitializeEventView.as_view(), name="init-event"),
    path("tickets/book/", BookTicketView.as_view(), name="book-ticket"),
    path("tickets/cancel/", CancelTicketView.as_view(), name="cancel-ticket"),
]
