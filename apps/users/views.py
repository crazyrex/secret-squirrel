from django.core.urlresolvers import reverse

from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.vary import vary_on_cookie

from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages

import jingo


@vary_on_cookie
def display_profile(request):
    return jingo.render(request, 'users/profile.html')


@vary_on_cookie
def edit_profile(request):
    return HttpResponse('edit profile page')


def register(request):
    """ Given a username, email, and password, creates a new user """

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account Created. Please login")
            return HttpResponseRedirect(reverse('cas_login'))
    else:
        form = UserCreationForm()

    return jingo.render(request, "users/register.html", {
        'form' : form,
    })
