import itertools
import operator
import random
import re
import time
import urllib
import urlparse

from django.conf import settings
from django.core import paginator
from django.core.serializers import json
from django.core.mail import send_mail as django_send_mail
from django.utils.functional import Promise
from django.utils.encoding import smart_str

import pytz

import commonware.log

log = commonware.log.getLogger('sso.utils')

def urlparams(url_, hash=None, **query):
    """
    Add a fragment and/or query paramaters to a URL.

    New query params will be appended to exising parameters, except duplicate
    names, which will be replaced.
    """
    url = urlparse.urlparse(url_)
    fragment = hash if hash is not None else url.fragment

    # Use dict(parse_qsl) so we don't get lists of values.
    q = url.query
    query_dict = dict(urlparse.parse_qsl(smart_str(q))) if q else {}
    query_dict.update((k, v) for k, v in query.items())

    query_string = urlencode([(k, v) for k, v in query_dict.items()
                             if v is not None])
    new = urlparse.ParseResult(url.scheme, url.netloc, url.path, url.params,
                               query_string, fragment)
    return new.geturl()


def isotime(t):
    """Date/Time format according to ISO 8601"""
    if not hasattr(t, 'tzinfo'):
        return
    return _append_tz(t).astimezone(pytz.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def epoch(t):
    """Date/Time converted to seconds since epoch"""
    if not hasattr(t, 'tzinfo'):
        return
    return int(time.mktime(_append_tz(t).timetuple()))


def _append_tz(t):
    tz = pytz.timezone(settings.TIME_ZONE)
    return tz.localize(t)


def sorted_groupby(seq, key):
    """
    Given a sequence, we sort it and group it by a key.

    key should be a string (used with attrgetter) or a function.
    """
    if isinstance(key, basestring):
        key = operator.attrgetter(key)
    return itertools.groupby(sorted(seq, key=key), key=key)


def paginate(request, queryset, per_page=20, count=None):
    """
    Get a Paginator, abstracting some common paging actions.

    If you pass ``count``, that value will be used instead of calling
    ``.count()`` on the queryset.  This can be good if the queryset would
    produce an expensive count query.
    """
    p = paginator.Paginator(queryset, per_page)

    if count is not None:
        p._count = count

    # Get the page from the request, make sure it's an int.
    try:
        page = int(request.GET.get('page', 1))
    except ValueError:
        page = 1

    # Get a page of results, or the first page if there's a problem.
    try:
        paginated = p.page(page)
    except (paginator.EmptyPage, paginator.InvalidPage):
        paginated = p.page(1)

    base = request.build_absolute_uri(request.path)

    paginated.url = u'%s?%s' % (base, request.GET.urlencode())
    return paginated


def send_mail(subject, message, from_email=None, recipient_list=None,
              fail_silently=False):
    """
    A wrapper around django.core.mail.send_mail.

    Adds blacklist checking and error logging.
    """
    if not recipient_list:
        return True

    if not from_email:
        from_email = settings.DEFAULT_FROM_EMAIL

    # Prune blacklisted emails.
    white_list = []
    for email in recipient_list:
        if email.lower() in settings.EMAIL_BLACKLIST:
            log.debug('Blacklisted email removed from list: %s' % email)
        else:
            white_list.append(email)
    try:
        if white_list:
            result = django_send_mail(subject, message, from_email, white_list,
                                      fail_silently=False)
        else:
            result = True
    except Exception as e:
        result = False
        log.error('send_mail failed with error: %s' % e)
        if not fail_silently:
            raise

    return result


class JSONEncoder(json.DjangoJSONEncoder):
    def default(self, obj):
        return super(JSONEncoder, self).default(obj)


# By Ned Batchelder.
def chunked(seq, n):
    """
    Yield successive n-sized chunks from seq.

    >>> for group in chunked(range(8), 3):
    ...     print group
    [0, 1, 2]
    [3, 4, 5]
    [6, 7]
    """
    for i in xrange(0, len(seq), n):
        yield seq[i:i+n]


def urlencode(items):
    """A Unicode-safe URLencoder."""
    try:
        return urllib.urlencode(items)
    except UnicodeEncodeError:
        return urllib.urlencode([(k, smart_str(v)) for k, v in items])


def randslice(qs, limit, exclude=None):
    """
    Get a random slice of items from ``qs`` of size ``limit``.

    There will be two queries.  One to find out how many elements are in ``qs``
    and another to get a slice.  The count is so we don't go out of bounds.
    If exclude is given, we make sure that pk doesn't show up in the slice.

    This replaces qs.order_by('?')[:limit].
    """
    cnt = qs.count()
    # Get one extra in case we find the element that should be excluded.
    if exclude is not None:
        limit += 1
    rand = 0 if limit > cnt else random.randint(0, cnt - limit)
    slice_ = list(qs[rand:rand + limit])
    if exclude is not None:
        slice_ = [o for o in slice_ if o.pk != exclude][:limit - 1]
    return slice_


slug_re = re.compile('[^\w\s-]', re.UNICODE)


def slugify(s):
    s = slug_re.sub('', unicode(s)).strip().lower()
    return re.sub('[-\s]+', '-', s)
