from django.core.urlresolvers import reverse

from jingo import register


@register.function
def url(viewname, *args, **kwargs):
    """Helper for Django's ``reverse`` in templates."""
    return reverse(viewname, args=args, kwargs=kwargs)
