import math
import os
import string

from cas_provider.models import ServiceTicket, LoginTicket

def _generate_string(length=8):
    """Generates a random string of the requested length. Used for creation of tickets."""
    assert length >= 0
    randlen = int(math.ceil(length/2.0))
    return os.urandom(randlen).encode('hex')[:length]

def create_service_ticket(user, service):
    """
    Creates a new service ticket for the specified user and service.
   Uses _generate_string.
    """
    ticket_string = 'ST-' + _generate_string(29) # Total ticket length = 29 + 3 = 32
    ticket = ServiceTicket(service=service, user=user, ticket=ticket_string)
    ticket.save()
    return ticket

def create_login_ticket():
    """Creates a new login ticket for the login form. Uses _generate_string."""
    ticket_string = 'LT-' + _generate_string(29)
    ticket = LoginTicket(ticket=ticket_string)
    ticket.save()
    return ticket_string

