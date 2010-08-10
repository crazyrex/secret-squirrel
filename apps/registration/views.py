""" Handles New Account creation for users """

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages




import jingo

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

    return jingo.render(request, "registration/register.html", {
        'form' : form,
    })
