import os
from xml.dom.minidom import Document

from django.http import HttpResponse

from cas_provider.models import ServiceTicket, LoginTicket

def _generate_string(length=8):
    """
    Generates a random string of the requested length. Used for creation of
    tickets.
    """
    assert length >= 0

    # Just enough randomness for our string length, hex-encoded.
    randlen = (length >> 1) + (length % 2)
    return os.urandom(randlen).encode('hex')[:length]


def create_service_ticket(user, service):
    """Creates a new service ticket for the specified user and service."""

    # Total ticket length = 29 + 3 = 32
    ticket_string = 'ST-' + _generate_string(29)
    ticket = ServiceTicket(service=service, user=user, ticket=ticket_string)
    ticket.save()
    return ticket


def create_login_ticket():
    """Creates a new login ticket for the login form."""
    ticket_string = 'LT-' + _generate_string(29)
    ticket = LoginTicket(ticket=ticket_string)
    ticket.save()
    return ticket_string

def unauthorized_cas_1_0(error_code='', error_message=''):
    return HttpResponse("no\n\n")

def unauthorized_cas_2_0(error_code='', error_message=''):
    """
    <cas:serviceResponse xmlns:cas='http://www.yale.edu/tp/cas'>
        <cas:authenticationFailure code="INVALID_TICKET">
	I pitty the fool with your Ticket, sucka
        </cas:authenticationFailure>
    </cas:serviceResponse>"""
    doc, resp = _prepare_response()

    authFailure = doc.createElement('cas:authenticationFailure')
    authFailure.setAttribute('code', error_code)
    authFailure.appendChild(doc.createTextNode(error_message))

    resp.appendChild(authFailure)

    return HttpResponse(resp.toxml('utf8'), 'application/xml')

def ok_cas_1_0(username):
    return HttpResponse("yes\n%s\n" % username)

def ok_cas_2_0(username):
    """
    <cas:serviceResponse xmlns:cas='http://www.yale.edu/tp/cas'>
        <cas:authenticationSuccess>
	    <cas:user>%s</cas:user>
        </cas:authenticationSuccess>
    </cas:serviceResponse>"""
    doc, resp = _prepare_response()

    authSuccess = doc.createElement('cas:authenticationSuccess')
    casUser = doc.createElement('cas:user')
    casUser.appendChild(doc.createTextNode(username))
    authSuccess.appendChild(casUser)

    resp.appendChild(authSuccess)
    return HttpResponse( resp.toxml('utf8'), 'application/xml')

def _prepare_response():
    doc = Document()
    resp = doc.createElementNS('http://www.yale.edu/tp/cas', 'cas:serviceResponse')
    resp.setAttribute('xmlns:cas', 'http://www.yale.edu/tp/cas') # seriously minidom?
    doc.appendChild(resp)
    return (doc, resp)
