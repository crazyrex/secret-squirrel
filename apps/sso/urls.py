from django.conf.urls.defaults import patterns, url
from django.views.generic.simple import direct_to_template

import jingo


urlpatterns = patterns('',
    # The homepage.
    url('^$', jingo.render, {'template': 'sso/home.html'},
        name='home'),
)
