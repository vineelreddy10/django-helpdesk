import requests
import requests.exceptions
import logging

from . import settings
from .signals import update_ticket_done

logger = logging.getLogger(__name__)

# listener is loaded via app.py HelpdeskConfig.ready()
@receiver(update_ticket_done)
def notify_followup_webhooks(sender, followup, **kwargs):
    urls = settings.HELPDESK_GET_FOLLOWUP_WEBHOOK_URLS()
    if not urls:
        return

    if sender == "update_ticket":
        # Serialize the ticket associated with the followup
        from .serializers import TicketSerializer
        ticket = followup.ticket
        ticket.set_custom_field_values()
        serialized_ticket = TicketSerializer(ticket).data

        # Prepare the data to send
        data = {
            'ticket': serialized_ticket,
            'queue_slug': ticket.queue.slug,
            'followup_id': followup.id
        }

        for url in urls:
            try:
                requests.post(url, json=data, timeout=settings.HELPDESK_WEBHOOK_TIMEOUT)
            except requests.exceptions.Timeout:
                logger.error('Timeout while sending followup webhook to %s', url)


def send_new_ticket_webhook(ticket):
    urls = settings.HELPDESK_GET_NEW_TICKET_WEBHOOK_URLS()
    if not urls:
        return
    # Serialize the ticket
    from .serializers import TicketSerializer
    ticket.set_custom_field_values()
    serialized_ticket = TicketSerializer(ticket).data

    # Prepare the data to send
    data = {
        'ticket': serialized_ticket,
        'queue_slug': ticket.queue.slug
    }

    for url in urls:
        try:
            requests.post(url, json=data, timeout=settings.HELPDESK_WEBHOOK_TIMEOUT)
        except requests.exceptions.Timeout:
            logger.error('Timeout while sending new ticket webhook to %s', url)
