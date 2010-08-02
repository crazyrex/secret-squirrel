from django.http import HttpResponse
from django.views.decorators.vary import vary_on_cookie

import jingo


@vary_on_cookie
def display_profile(request):
    return jingo.render(request, 'users/profile.html')


@vary_on_cookie
def edit_profile(request):
    return HttpResponse('edit profile page')
