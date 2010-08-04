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
from .utils import create_service_ticket


log = logging.getLogger('sso.login')


def _login(request, template_name='cas/login.html',
          success_redirect=settings.LOGIN_REDIRECT_URL):
    """
    Standard CAS login form.

    Instead of running this directly, we enforce a service whitelist first.
    See whitelist_login().
    """

    service = request.GET.get('service', None)
    if request.user.is_authenticated():
        if service is not None:
            ticket = create_service_ticket(request.user, service)
            if service.find('?') == -1:
                return HttpResponseRedirect(service + '?ticket=' + ticket.ticket)
            else:
                return HttpResponseRedirect(service + '&ticket=' + ticket.ticket)
        else:
            return HttpResponseRedirect(success_redirect)

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
                        ticket = create_service_ticket(user, service)
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
    service = request.GET.get('service', None)
    ticket_string = request.GET.get('ticket', None)
    if service is not None and ticket_string is not None:
        try:
            ticket = ServiceTicket.objects.get(ticket=ticket_string)
            assert not ticket.service or ticket.service == service
            username = ticket.user.username
            ticket.delete()
            return HttpResponse("yes\n%s\n" % username)
        except:
            pass
    return HttpResponse("no\n\n")


def logout(request, template_name='cas/logout.html'):
    url = request.GET.get('url', None)
    auth_logout(request)
    return jingo.render(request, template_name, {'return_url': url})
