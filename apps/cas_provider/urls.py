from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('cas_provider.views',
    url(r'^login/?$', 'whitelist_login', name='cas_login'),
    url(r'^validate/?$', 'validate', name='cas_validate'),
    url(r'^logout/?$', 'logout', {'template_name': 'users/logout.html'},
        name='cas_logout'),
)
