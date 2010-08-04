from django.conf import settings
from django.conf.urls.defaults import *
from django.contrib import admin


admin.autodiscover()

urlpatterns = patterns('',
    ('', include('sso.urls')),

    # Hook up login/logout separately from the following apps

    # Login through service whitelist
    # Users
    ('', include('users.urls')),

    url(r'^users/login/?$', 'sso.views.whitelist_login'),
    #url(r'^users/logout/?$', 'cas_provider.views.logout', {
    #    'template_name': 'users/logout.html'}),

    (r'^profile/', include('users.urls')),
    #(r'^users/', include('cas_provider.urls')),
    url(r'^users/login/?$', 'login', name='cas_login'), #aok

    (r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    media_url = settings.MEDIA_URL.lstrip('/').rstrip('/')
    urlpatterns += patterns('',
        (r'^%s/(?P<path>.*)$' % media_url, 'django.views.static.serve',
          {'document_root': settings.MEDIA_ROOT}),
    )
