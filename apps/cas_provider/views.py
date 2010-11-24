from datetime import datetime, timedelta
import logging
from urlparse import urlparse

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login, logout as auth_logout

import jingo

from sso.models import ClientSite

from .forms import LoginForm
from .models import ServiceTicket, LoginTicket, auth_success_response
import utils

log = logging.getLogger('sso.login')

"""
Notes on CAS 1.0 versus 2.0
1.0
  login
  validate
  TGC - Ticket Granting Cookie
  ST  - Service Ticket
  Plain text response format

2.0 Adds the following:
  XML response format
  gateway parameter - Checks for Authentication but doesn't force login
  renew parameter   - Force login no matter what

2.0 features which are *not implemented* in secret-squirrel cas_provider:
  Proxy/Target
  PGT - Proxy Granting Ticket
  PGTIOU - Proxy Granting Ticket I Owe you
  PT - Proxy Ticket
"""

def _login(request, template_name='cas/login.html',
          success_redirect=settings.LOGIN_REDIRECT_URL):
    """
    Standard CAS login form.

    Instead of running this directly, we enforce a service whitelist first.
    See whitelist_login().
    """

    service = request.GET.get('service', None)
    # renew=true indicates that we should force the user to log in.
    if False == request.GET.get('renew', False) and request.user.is_authenticated():
        if service is not None:
            ticket = utils.create_service_ticket(request.user, service)
            # TODO Parsing and rebuilding the URL here is a much better idea.
            if service.find('?') == -1:
                return HttpResponseRedirect(service + '?ticket=' + ticket.ticket)
            else:
                return HttpResponseRedirect(service + '&ticket=' + ticket.ticket)
        else:
            return HttpResponseRedirect(success_redirect)

    # gateway=true indicates that we should silently try to authenticate (no
    # login screen).
    if request.GET.get('gateway', False):
        return HttpResponseRedirect(service)
    errors = []
    if request.method == 'POST':
        username = request.POST.get('username', None)
        password = request.POST.get('password', None)
        service = request.POST.get('service', None)
        lt = request.POST.get('lt', None)

        try:
            login_ticket = LoginTicket.objects.get(ticket=lt)
        except:
            errors.append('Login ticket expired. Please try again.')
        else:
            login_ticket.delete()
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    auth_login(request, user)
                    if service is not None:
                        ticket = utils.create_service_ticket(user, service)
                        return HttpResponseRedirect(service + '?ticket=' + ticket.ticket)
                    else:
                        return HttpResponseRedirect(success_redirect)
                else:
                    errors.append('This account is disabled.')
            else:
                    errors.append('Incorrect username and/or password.')
    form = LoginForm(service)
    return jingo.render(request, template_name,
                        {'form': form, 'errors': errors})


def whitelist_login(request, *args, **kwargs):
    """
    Run service requests against whitelist before serving them through the
    CAS provider.
    """
    service = request.GET.get('service', '')
    parsed = urlparse(service)
    if not service or not parsed.netloc:
        return _login(request, *args, **kwargs)

    try:
        site = ClientSite.objects.get(domain=parsed.netloc)
    except ClientSite.DoesNotExist:
        log.warning('Login request for invalid service URL %s' % service)
        return HttpResponseForbidden('Invalid service URL.')

    response = _login(request, *args, **kwargs)

    # Associate user with this service
    if (request.user.is_authenticated() and
        isinstance(response, HttpResponseRedirect)):
            try:
                usersite = request.user.sites.get(pk=site.pk)
            except ClientSite.DoesNotExist:
                site.users.add(request.user)
                log.debug(
                    'First-time association of user %s with service %s' % (
                        request.user.username, site.domain))

    return response



def validate(request):
    """ CAS 1.0 Callback to validate a Service Ticket (ST)"""
    return _common_validate(request, utils.unauthorized_cas_1_0, utils.ok_cas_1_0)

def service_validate(request):
    """ CAS 2.0 Callback to validate a Service Ticket (ST)"""
    return _common_validate(request, utils.unauthorized_cas_2_0, utils.ok_cas_2_0)

def _common_validate(request, failed_fn, success_fn):
    """ Common Validation logic which will either fail or succeed.
        request - Django request
        failed_fn - A function which takes two optional parameters
                    (string error code and string error message)
                    and returns a HttpResponse
        success_fn - A function which takes one argument
                    (string username) and returns a HttpResponse
        The HttpResponse must be a valid CAS response
    """
    service = request.GET.get('service', None)
    ticket_string = request.GET.get('ticket', None)

    if service is None:
        return failed_fn('INVALID_SERVICE', 'Missing service parameter')
    if ticket_string is None:
        return failed_fn('INVALID_TICKET', 'Missing ticket parameter')

    try:
        ticket = ServiceTicket.objects.get(ticket=ticket_string)
    except ServiceTicket.DoesNotExist:
        log.warning('INVALID Validation request for unknown ticket. Ticket: %s' % (
            ticket_string))
        return failed_fn('INVALID_TICKET', 'Ticket [%s] is not valid' % ticket_string)

    # Issued-for and validating service must match
    if not ticket.service or ticket.service not in service:
        error_message = "INVALID Service [%s] tried to validate a ticket issued for [%s]." % (
            service, ticket.service)
        log.warning(error_message)
        # TODO... this is failing because mod_auth_cas is appending an extra title parameter causing this to fail...
        return failed_fn('INVALID_SERVICE', error_message)

    # Ticket must not be expired.
    try:
        assert (settings.SERVICE_TICKET_TIMEOUT == 0 or
                ticket.created > (datetime.now() - (
                    timedelta(seconds=settings.SERVICE_TICKET_TIMEOUT))))
    except AssertionError:
        error_message = "INVALID Validation request for expired ticket. Service: %s. Ticket: %s User: %s" % (
            ticket.service, ticket_string, ticket.user.username)
        log.warning(error_message)
        ticket.delete()
        return failed_fn('INVALID_TICKET', error_message)

    # Everything all right. Delete ticket, return success message.
    username = ticket.user.username
    ticket.delete()
    return success_fn(username, ticket.user.userprofile.sso_uuid)


def logout(request, template_name='cas/logout.html'):
    url = request.GET.get('url', None)
    auth_logout(request)
    return jingo.render(request, template_name, {'return_url': url})
