from django.conf.urls.defaults import patterns, url

from registration.views import register

urlpatterns = patterns('',
    url(r'^$', register, name='sso_register'),
)
